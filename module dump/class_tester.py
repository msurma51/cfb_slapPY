class possession:
    count = 0
    'Stores and tracks possession throughout game parsing'
    def __init__(self,home_team,away_team):
        self.home = home_team
        self.away = away_team
        self.teams = (home_team,away_team)
        self.ball = None
    def set(self,poss_team):
        if poss_team in self.teams:
            self.ball = poss_team
    def get(self):
        return(self.ball)
    def flip(self):
        if self.ball == self.home:
            self.ball = self.away
            possession.count += 1
        elif self.ball == self.away:
            self.ball = self.home
            possession.count += 1

poss = possession('ALV','LYC')
#poss.set('LYC')
print(poss.get())
poss.flip()
print(poss.get())

