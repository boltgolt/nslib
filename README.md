# nslib 0.0.2

Library to interact with the Dutch Railways (Nederlandse Spoorwegen).

### Usage

```python
# Initialize nslib
ns = Nslib()

# Current and planned disruptions on the rail network
ns.disruptions

# Get departing trains from a station
ns.getDepartures("RTB")
# Get route options between 2 to 3 points
ns.getRoute(["LC", "MG", "RTB"])

# Log into a NS account
account = ns.Account("email", "password")

for card in account.cards:
	# OV-Chipcard number
	card.number
	# Whether or not the card is currently checked in
	card.checkedIn
	# Last known account balance
	card.balance
	# Last known trips
	card.trips
```

The official station codes have to be used for `getDepartures` and `getRoute` , the full list of codes can be found  [here](https://en.wikipedia.org/wiki/Railway_stations_in_the_Netherlands#List_of_stations,_with_their_official_abbreviations).
