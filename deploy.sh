echo "deploying"
daphne -b 0.0.0.0 -p 443 testing_game.asgi:application