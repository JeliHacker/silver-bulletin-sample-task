# Marginal Wins Lost to Injury in the NBA

## Methodology
We use two datasources: Basketball-Reference for advanced player stats such as VORP (which we convert to WAR),
and Spotrac for injury data, such as games missed. We first get the number of missed wins a player cost their team due to injuries with the following formula: 
WAR per minute * minutes per game * games missed = wins lost to injury 
then we add up the results for all the players on a team to get that team's total wins lost due to injury. 

## Instructions for running code
To get a CSV file of the final results:<br>
`python main.py 2025 wins_lost_to_injury.csv`

To get a CSV file of the Basketball-Reference advanced player data:<br>
`python3 scrape_bref_ws48.py 2025 > player_stats_2024-2025.csv`

To get a CSV file of the Spotrac injury data:<br>
`python scrape_spotrac_injuries.py 2024 > injuries_2024-2025.csv`

Note that Spotrac uses the beginning year for a season while the other two use the later year. So if you want 2023-2024 data, use 2023 for scrape_spotrac_injuries.py and 2024 for main.py and scrape_bref_ws48.py
## Current Limitations
Basketball-Reference separated the data nicely for players who were traded, but Spotrac did not. 
So there wasn't an easy way to track games missed for players who were traded in the middle of the season.
My quick fix was to prorate injuries as a share of minutes played. 
So if a player missed 10 games total, and played 75% of their minutes for the Lakers and 25% for the Cavs, they'll have 7.5 missed games for the Laker and 2.5 for the Cavs.
This obviously isn't perfect (a major example is it undercounts Anthony Davis's injuries on the Mavericks), so a better long term solution would involve bringing in either trade data (like the date a player was traded) or game by game data to determine more precisely which games were missed when.


## Results
The biggest standout here is that OKC missed out on 17 1/2 wins due to injury. 
In some ways this makes sense (Chet Holmgren is probably the third best player and missed 50 games), but observant fans will note that adding 17 wins to the 68 games the team actually won sums to 85 wins in an 82 game season, which is impossible.   
Running the model for previous years reinforces that the wins-lost totals are probably too high (26 missed wins for the 76ers last season would put them at 73 total, 19 wins for dallas last season would've given them 69, etc.)
There's a couple of reasons this model is overestimating wins lost to injury: double counting minutes, and baking in too poor of a replacement level player. 

There are only 240 (48 * 5) total minutes in a game for all the players on a team, and the model doesn't do anything to account for this. A solution could be to go game by game and set a cap of 240 on the minutes per game we're adding back, or even less than that.<br>
And then for the level of play from the replacement player, VORP uses -2 BPM (Box Plus/Minus). In the case of a deep team like the Thunder, this isn't a good assumption because they will likely get better than -2 BPM play from whoever replaces Holmgren's minutes on a given night. So the solution here could be to recompute VORP and WAR with different assumptions.  

Even with inflated totals, the potential headline is still that the Thunder had a *very* impressive season, and were potentially held back from a 70+ win season by injuries. 
![5G87C-wins-lost-to-injury-for-the-2024-2025-nba-season](https://github.com/user-attachments/assets/eb622f4b-35ff-4a6c-8693-e6f93e91cb43)
