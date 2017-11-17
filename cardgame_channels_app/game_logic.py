"""Card Game Logic"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.utils.crypto import get_random_string

from .models import *


def add_player_to_game(game_code, player_name):
    """Creates a new Person object and adds to an existing game"""
    game = Game.objects.get(code=game_code)
    player = Player.objects.create(name=player_name, game=game)
    draw_card(game, player, 'red', 5)
    if not CardGamePlayer.objects.filter(game=game, status='matching'):
        # draw green card for new player if no one is currently the judge (and make them the judge)
        draw_card(game, player)
        player.status = Player.JUDGE
        player.save()
    return player


def create_game_code():
    """Create a Unique Game Code"""
    game_code = ""
    not_a_unique_code = True
    while not_a_unique_code:
        game_code = get_random_string(4, allowed_chars='abcdefghijklmnopqrstuvwxyz')
        try:
            Game.objects.create(code=game_code)
            not_a_unique_code = False

        except IntegrityError:
            not_a_unique_code = True
    return game_code


def draw_card(game, player=None, color=Card.GREEN, count=1):
    """Draws a random card that has not been used already"""
    if color == Card.GREEN:
        status = CardGamePlayer.MATCHING
    else:
        status = CardGamePlayer.HAND
    draw_again = True
    while draw_again:
        draw_again = False
        used_cards = CardGamePlayer.objects.filter(game=game).values_list('card__id', flat=True)
        cards = Card.objects.exclude(id__in=used_cards).filter(type=color).order_by('?')[:count]
        for card in cards:
            try:
                CardGamePlayer.objects.create(
                    card=card,
                    game=game,
                    player=player,
                    status=status
                )
            except IntegrityError:
                draw_again = True  # Try Again


def get_all_players_submitted(game_code):
    """Returns true or false that all the players have submitted their cards to the judge"""
    try:
        waiting_players = Player.objects.filter(game__code=game_code, status=Player.WAITING)
        return False if waiting_players else True
    except ObjectDoesNotExist:
        return True


def get_cards_in_hand_values_list(player):
    """Gets all the cards in a players's hand and return as a values list"""
    return list(Card.objects.filter(cardgameplayer__player=player, cardgameplayer__status=CardGamePlayer.HAND).values('pk', 'name', 'text'))


def get_game_player_values_list(game_code):
    """Gets the players for a game_code and return as values list"""
    return list(Player.objects.values('pk', 'name', 'status', 'score').filter(game__code=game_code))


def get_judge_player_values(game_code):
    """Gets the judge a game_code and return as values"""
    return Player.objects.values('pk', 'name', 'status', 'score').get(game__code=game_code, status=Player.JUDGE)


def get_matching_card_values(game_code):
    """Gets the matching card for a game_code and return as values"""
    card = Card.objects.values('pk', 'name', 'text').get(cardgameplayer__game__code=game_code, cardgameplayer__status=CardGamePlayer.MATCHING)
    card['status'] = 'matching'
    return card


def get_player_values(player_pk):
    """Gets a values version of a player"""
    return Player.objects.values('pk', 'name', 'status', 'score').get(pk=player_pk)


def get_card_values(game_code, card):
    """Gets a values version of a card"""
    return Card.objects.values('pk', 'name', 'text').get(pk=card.pk, cardgameplayer__game__code=game_code)


def get_submitted_cards_values_list(game_code):
    """Gets all the submitted cards for a game_code and return as a values list"""
    return list(Card.objects.filter(cardgameplayer__game__code=game_code, cardgameplayer__status=CardGamePlayer.SUBMITTED).values('pk', 'name', 'text'))


def pick_card(game_code, card_pk):
    """Marks a CardGamePlayer as picked by the Judge"""
    game = Game.objects.get(code=game_code)

    # Assign Picked Card as Winnings
    green_card = CardGamePlayer.objects.get(game=game, status=CardGamePlayer.MATCHING)
    green_card.status = CardGamePlayer.WON
    green_card.save()

    # Set everyone back to being a player
    Player.objects.filter(game=game).update(status=Player.WAITING)

    # Put the card that was picked into the backlog, and assign winner as judge
    cgp = CardGamePlayer.objects.get(game=game, card__pk=card_pk)
    cgp.status = CardGamePlayer.PICKED
    cgp.save()

    cgp.player.score += 1
    cgp.player.status = Player.JUDGE
    cgp.player.save()

    # Mark non-winning cards as losers
    CardGamePlayer.objects.filter(game=cgp.game, status=CardGamePlayer.SUBMITTED).update(status=CardGamePlayer.LOST)

    replenish_hands(cgp.game.code)
    draw_card(game=cgp.game, player=cgp.player)  # New Green Card to Picked Player
    return cgp


def replenish_hands(game_code):
    """Replenishes the hands of all players in the game"""
    game = Game.objects.get(code=game_code)
    for player in game.players.all():
        hand_card_count = player.cardgameplayer_set.filter(status='hand').count()
        if hand_card_count < 5:
            draw_card(game, player, color='red', count=(5 - hand_card_count))


def submit_card(game_code, card_pk):
    """Submits a CardGamePlayer to the Judge"""
    game = Game.objects.get(code=game_code)
    cgp = CardGamePlayer.objects.get(game=game, card__pk=card_pk)
    cgp.status = CardGamePlayer.SUBMITTED
    cgp.save()
    cgp.player.status = Player.SUBMITTED
    cgp.player.save()
    return cgp
