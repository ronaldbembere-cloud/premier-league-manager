"""PREMIER LEAGUE - refreshed Tkinter football league manager.
Teams must have a stadium. Fixtures use a two-leg round-robin schedule:
every team meets every other team once in each leg, with home/away reversed.
Saved data is kept in Documents/Premier League/league_data.json.
"""
import json, tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from itertools import combinations
import random

APP_TITLE = "PREMIER LEAGUE"
MIN_TEAMS = 2
DATA_DIR = Path.home() / "Documents" / "Premier League"
DATA_FILE = DATA_DIR / "league_data.json"
BG = "#0b1220"
PANEL = "#121d2f"
PANEL2 = "#19283d"
GREEN = "#25d366"
TEXT = "#eef4fb"
MUTED = "#a9b8ca"


def make_schedule(teams):
    """Generate a complete two-leg round-robin schedule.

    Even team count: N-1 matchweeks per leg.
    Odd team count: N matchweeks per leg, with one bye each week.
    The second leg reverses every first-leg home/away pairing.
    """
    teams = list(teams)
    n = len(teams)
    if n < 2:
        return []
    random.shuffle(teams)
    rotation = teams[:]
    if n % 2:
        rotation.append(None)
    total_slots = len(rotation)
    weeks_per_leg = total_slots - 1
    first_leg = []
    for round_index in range(weeks_per_leg):
        matches = []
        for i in range(total_slots // 2):
            left, right = rotation[i], rotation[total_slots - 1 - i]
            if left is None or right is None:
                continue
            home, away = (right, left) if (round_index + i) % 2 else (left, right)
            matches.append({
                "week": round_index + 1, "leg": "First Leg",
                "home": home, "away": away, "played": False,
                "home_goals": None, "away_goals": None,
            })
        first_leg.extend(matches)
        rotation = [rotation[0], rotation[-1], *rotation[1:-1]]
    second_leg = [{
        "week": match["week"] + weeks_per_leg,
        "leg": "Second Leg",
        "home": match["away"], "away": match["home"],
        "played": False, "home_goals": None, "away_goals": None,
    } for match in first_leg]
    return first_leg + second_leg


def calculate_table(teams, fixtures):
    table = {t: {"P":0,"W":0,"D":0,"L":0,"GF":0,"GA":0,"GD":0,"Pts":0} for t in teams}
    for m in fixtures:
        if not m.get("played") or m["home"] not in table or m["away"] not in table: continue
        h, a = table[m["home"]], table[m["away"]]
        hg, ag = int(m["home_goals"]), int(m["away_goals"])
        h["P"] += 1; a["P"] += 1; h["GF"] += hg; h["GA"] += ag; a["GF"] += ag; a["GA"] += hg
        if hg > ag: h["W"] += 1; h["Pts"] += 3; a["L"] += 1
        elif hg < ag: a["W"] += 1; a["Pts"] += 3; h["L"] += 1
        else: h["D"] += 1; a["D"] += 1; h["Pts"] += 1; a["Pts"] += 1
    for s in table.values(): s["GD"] = s["GF"] - s["GA"]
    return table


class PremierLeagueApp:
    def __init__(self, root):
        self.root = root; root.title(APP_TITLE); root.geometry("1240x780"); root.minsize(980, 650); root.configure(bg=BG)
        self.teams = {}; self.fixtures = []; self.selected_fixture = None; self.active_page = "Dashboard"
        self.status = tk.StringVar(value="Ready")
        self.style()
        self.load_data()
        if not self.teams: self.show_setup()
        else: self.show_dashboard()

    def style(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure("Treeview", background=PANEL, foreground=TEXT, fieldbackground=PANEL, rowheight=30, borderwidth=0, font=("Segoe UI", 10))
        s.configure("Treeview.Heading", background=PANEL2, foreground=TEXT, font=("Segoe UI", 10, "bold"), relief="flat")
        s.map("Treeview", background=[("selected", "#245b45")], foreground=[("selected", "white")])
        s.configure("TCombobox", padding=5)

    def load_data(self):
        try:
            if not DATA_FILE.exists(): return
            d = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            old = d.get("teams", [])
            if isinstance(old, list): self.teams = {t: "Stadium not set" for t in old}
            elif isinstance(old, dict): self.teams = old
            else: self.teams = {}
            self.fixtures = d.get("fixtures", [])
            # Upgrade older schedules automatically, keeping any scores already entered.
            if len(self.teams) >= 2 and self.fixtures and any("leg" not in m for m in self.fixtures):
                saved_results = {
                    (m.get("home"), m.get("away")): m
                    for m in self.fixtures if m.get("played")
                }
                self.fixtures = make_schedule(list(self.teams))
                for m in self.fixtures:
                    old_match = saved_results.get((m["home"], m["away"]))
                    if old_match:
                        m.update(played=True,
                                 home_goals=old_match.get("home_goals"),
                                 away_goals=old_match.get("away_goals"))
                self.save_data()
            else:
                for m in self.fixtures:
                    m.setdefault("week", 1)
                    m.setdefault("leg", "First Leg")
            # Existing legacy data may lack stadiums; user can add them on Teams page.
        except (OSError, ValueError, TypeError): self.teams, self.fixtures = {}, []

    def save_data(self):
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            DATA_FILE.write_text(json.dumps({"teams":self.teams,"fixtures":self.fixtures}, indent=2), encoding="utf-8")
            self.status.set("Saved locally • Documents / Premier League")
        except OSError as e: messagebox.showerror("Save error", str(e))

    def clear(self):
        for w in self.root.winfo_children(): w.destroy()

    def show_setup(self):
        self.clear(); self.root.configure(bg=BG)
        outer = tk.Frame(self.root, bg=BG, padx=34, pady=24); outer.pack(fill="both", expand=True)
        tk.Label(outer, text="⚽  PREMIER LEAGUE", bg=BG, fg=GREEN, font=("Segoe UI", 25, "bold")).pack(anchor="w")
        tk.Label(outer, text="Create your competition • Every club needs a home ground", bg=BG, fg=MUTED, font=("Segoe UI", 11)).pack(anchor="w", pady=(4,18))
        tk.Label(outer, text="Enter one team and its stadium per row. Use a | between the two.", bg=BG, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(outer, text="Example: Arsenal | Emirates Stadium", bg=BG, fg=MUTED).pack(anchor="w", pady=(4,8))
        self.setup_text = tk.Text(outer, bg=PANEL, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Consolas", 12), height=14, padx=12, pady=10)
        self.setup_text.pack(fill="both", expand=True, pady=8)
        self.setup_text.insert("1.0", "Arsenal | Emirates Stadium\nChelsea | Stamford Bridge\nLiverpool | Anfield\nManchester City | Etihad Stadium\nManchester United | Old Trafford")
        row = tk.Frame(outer, bg=BG); row.pack(fill="x", pady=12)
        self.button(row, "CREATE LEAGUE  →", self.create_league, green=True).pack(side="left")
        if self.teams: self.button(row, "Cancel", self.show_dashboard).pack(side="left", padx=10)
        tk.Label(outer, text="Scheduling rule: two round-robin legs; every team meets every opponent twice, home and away.", bg=BG, fg=MUTED).pack(anchor="w")

    def create_league(self):
        teams = {}
        for line in self.setup_text.get("1.0", "end").splitlines():
            if not line.strip(): continue
            if "|" not in line:
                messagebox.showerror("Missing stadium", f"Add a stadium using Team Name | Stadium Name:\n{line}"); return
            name, stadium = [x.strip() for x in line.split("|", 1)]
            if not name or not stadium:
                messagebox.showerror("Missing information", "Every row needs both a team name and a stadium name."); return
            if name.casefold() in {x.casefold() for x in teams}:
                messagebox.showerror("Duplicate team", f"The team {name} is listed more than once."); return
            teams[name] = stadium
        if len(teams) < MIN_TEAMS:
            messagebox.showerror("Not enough teams", f"Register at least {MIN_TEAMS} teams."); return
        if self.teams and not messagebox.askyesno("Replace competition?", "Starting a new league replaces the current teams and results. Continue?"): return
        self.teams = teams; self.fixtures = make_schedule(list(teams)); self.selected_fixture = None
        self.save_data(); self.show_dashboard()

    def button(self, parent, text, command, green=False):
        return tk.Button(parent, text=text, command=command, bg=GREEN if green else PANEL2, fg="#07120c" if green else TEXT,
                         activebackground="#6af09a" if green else "#263b55", activeforeground=TEXT, relief="flat", bd=0,
                         padx=14, pady=9, font=("Segoe UI", 10, "bold"), cursor="hand2")

    def show_dashboard(self, page="Dashboard"):
        self.active_page = page; self.clear(); self.root.configure(bg=BG)
        shell = tk.Frame(self.root, bg=BG); shell.pack(fill="both", expand=True)
        side = tk.Frame(shell, bg="#080e19", width=218); side.pack(side="left", fill="y"); side.pack_propagate(False)
        tk.Label(side, text="⚽  PL MANAGER", bg="#080e19", fg=GREEN, font=("Segoe UI", 17, "bold"), pady=25).pack()
        tk.Label(side, text="COMPETITION CENTRE", bg="#080e19", fg="#71839a", font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=18, pady=(4,8))
        for label in ["Dashboard", "League Table", "Fixtures & Results", "Teams & Stadiums", "Competition History"]:
            self.button(side, ("●  " if page == label else "   ") + label, lambda p=label: self.show_dashboard(p), green=(page == label)).pack(fill="x", padx=12, pady=4)
        tk.Label(side, text="PREMIER LEAGUE\nSeason workspace", bg="#080e19", fg="#71839a", font=("Segoe UI", 9), pady=22).pack(side="bottom")
        main = tk.Frame(shell, bg=BG, padx=24, pady=18); main.pack(side="left", fill="both", expand=True)
        top = tk.Frame(main, bg=BG); top.pack(fill="x")
        tk.Label(top, text=page, bg=BG, fg=TEXT, font=("Segoe UI", 23, "bold")).pack(side="left")
        self.button(top, "+ NEW LEAGUE", self.show_setup).pack(side="right")
        tk.Label(main, text="Your competition at a glance", bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(3,16))
        if page == "Dashboard": self.build_home(main)
        elif page == "League Table": self.build_table(main)
        elif page == "Fixtures & Results": self.build_fixtures(main)
        elif page == "Teams & Stadiums": self.build_teams(main)
        else: self.build_history(main)
        tk.Label(self.root, textvariable=self.status, bg="#080e19", fg=MUTED, anchor="w", padx=12, pady=6).pack(fill="x", side="bottom")

    def card(self, parent, title, value, hint):
        f = tk.Frame(parent, bg=PANEL, padx=16, pady=13, highlightbackground="#23334a", highlightthickness=1)
        tk.Label(f, text=title.upper(), bg=PANEL, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(f, text=value, bg=PANEL, fg=GREEN, font=("Segoe UI", 23, "bold")).pack(anchor="w", pady=3)
        tk.Label(f, text=hint, bg=PANEL, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")
        return f

    def tree(self, parent, cols, heads, widths):
        box = tk.Frame(parent, bg=PANEL); box.pack(fill="both", expand=True, pady=6)
        t = ttk.Treeview(box, columns=cols, show="headings")
        for c,h,w in zip(cols,heads,widths): t.heading(c,text=h); t.column(c,width=w,minwidth=60,anchor="center")
        sy=ttk.Scrollbar(box,orient="vertical",command=t.yview); t.configure(yscrollcommand=sy.set)
        t.pack(side="left",fill="both",expand=True); sy.pack(side="right",fill="y")
        return t

    def build_home(self, parent):
        played=sum(bool(m.get("played")) for m in self.fixtures); total=len(self.fixtures)
        cards=tk.Frame(parent,bg=BG); cards.pack(fill="x")
        for title,value,hint in [("Clubs",str(len(self.teams)),"Registered teams"),("Fixtures",str(total),"Home and away matches"),("Played",str(played),"Results entered"),("Match weeks",str(max([m.get('week',1) for m in self.fixtures],default=0)),"Both legs combined")]:
            self.card(cards,title,value,hint).pack(side="left",fill="x",expand=True,padx=(0,10))
        tk.Label(parent,text="LATEST FIXTURES",bg=BG,fg=TEXT,font=("Segoe UI",13,"bold")).pack(anchor="w",pady=(24,4))
        t=self.tree(parent,("week","match","stadium","score"),("WEEK","MATCH","HOME STADIUM","SCORE"),(80,360,240,100))
        for m in self.fixtures[:8]: t.insert("","end",values=(f"{m.get('leg', 'First Leg')} • Week {m.get('week',1)}",f"{m['home']}  vs  {m['away']}",self.teams.get(m['home'],'Stadium not set'),f"{m['home_goals']} - {m['away_goals']}" if m.get('played') else "—"))
        if self.fixtures and all(m.get("played") for m in self.fixtures):
            ranked=self.ranked(); tk.Label(parent,text=f"🏆 CHAMPIONS: {ranked[0]}",bg=PANEL,fg=GREEN,font=("Segoe UI",15,"bold"),padx=14,pady=12).pack(fill="x",pady=12)

    def ranked(self):
        stats=calculate_table(list(self.teams),self.fixtures)
        return sorted(self.teams,key=lambda t:(stats[t]["Pts"],stats[t]["GD"],stats[t]["GF"],stats[t]["W"]),reverse=True)

    def build_table(self,parent):
        cols=("Pos","Team","P","W","D","L","GF","GA","GD","Pts")
        t=self.tree(parent,cols,cols,(55,260,55,55,55,55,60,60,60,70))
        stats=calculate_table(list(self.teams),self.fixtures)
        for pos,team in enumerate(self.ranked(),1):
            s=stats[team]; t.insert("","end",values=(pos,team,s['P'],s['W'],s['D'],s['L'],s['GF'],s['GA'],s['GD'],s['Pts']))
        tk.Label(parent,text="Ranking: Points → Goal Difference → Goals For → Wins",bg=BG,fg=MUTED).pack(anchor="w",pady=8)

    def build_fixtures(self,parent):
        bar=tk.Frame(parent,bg=BG); bar.pack(fill="x")
        self.leg_filter=tk.StringVar(value="All legs")
        leg_cb=ttk.Combobox(bar,textvariable=self.leg_filter,
                            values=["All legs", "First Leg", "Second Leg"],
                            state="readonly",width=16)
        leg_cb.pack(side="left",pady=5,padx=(0,8))
        leg_cb.bind("<<ComboboxSelected>>",lambda e:self.refresh_fixture_tree())
        self.week_filter=tk.StringVar(value="All match weeks")
        values=["All match weeks"]+[f"Match Week {w}" for w in sorted({m.get('week',1) for m in self.fixtures})]
        cb=ttk.Combobox(bar,textvariable=self.week_filter,values=values,state="readonly",width=22)
        cb.pack(side="left",pady=5)
        cb.bind("<<ComboboxSelected>>",lambda e:self.refresh_fixture_tree())
        self.fixture_tree=self.tree(parent,("week","home","stadium","score","away","awaystadium","status"),("WEEK","HOME","HOME STADIUM","SCORE","AWAY","AWAY STADIUM","STATUS"),(90,150,190,80,150,190,90))
        self.fixture_tree.bind("<<TreeviewSelect>>",self.select_fixture)
        form=tk.Frame(parent,bg=PANEL,padx=12,pady=12); form.pack(fill="x",pady=8)
        tk.Label(form,text="Selected match score",bg=PANEL,fg=TEXT,font=("Segoe UI",11,"bold")).grid(row=0,column=0,columnspan=4,sticky="w",pady=(0,8))
        self.detail=tk.StringVar(value="Select a fixture above")
        tk.Label(form,textvariable=self.detail,bg=PANEL,fg=GREEN).grid(row=1,column=0,columnspan=4,sticky="w",pady=(0,6))
        tk.Label(form,text="Home goals",bg=PANEL,fg=TEXT).grid(row=2,column=0,sticky="w"); self.hg=tk.Entry(form,width=8); self.hg.grid(row=2,column=1,padx=6)
        tk.Label(form,text="Away goals",bg=PANEL,fg=TEXT).grid(row=2,column=2,sticky="w"); self.ag=tk.Entry(form,width=8); self.ag.grid(row=2,column=3,padx=6)
        self.button(form,"SAVE RESULT",self.save_result,green=True).grid(row=2,column=4,padx=10)
        self.refresh_fixture_tree()

    def refresh_fixture_tree(self):
        if not hasattr(self,"fixture_tree"): return
        self.fixture_tree.delete(*self.fixture_tree.get_children())
        f=self.week_filter.get()
        for i,m in enumerate(self.fixtures):
            selected_leg = self.leg_filter.get() if hasattr(self, "leg_filter") else "All legs"
            if selected_leg != "All legs" and m.get("leg", "First Leg") != selected_leg: continue
            if f!="All match weeks" and f!=f"Match Week {m.get('week',1)}": continue
            self.fixture_tree.insert("","end",iid=str(i),values=(f"{m.get('leg', 'First Leg')} • {m.get('week',1)}",m['home'],self.teams.get(m['home'],'Stadium not set'),f"{m['home_goals']} - {m['away_goals']}" if m.get('played') else "—",m['away'],self.teams.get(m['away'],'Stadium not set'),"Played" if m.get('played') else "Upcoming"))

    def select_fixture(self,event=None):
        sel=self.fixture_tree.selection()
        if not sel:return
        self.selected_fixture=int(sel[0]); m=self.fixtures[self.selected_fixture]
        self.detail.set(f"{m.get('leg', 'First Leg')} • Match Week {m.get('week',1)} • {m['home']} ({self.teams.get(m['home'],'Stadium not set')}) vs {m['away']}")
        self.hg.delete(0,'end'); self.ag.delete(0,'end')
        if m.get('played'): self.hg.insert(0,str(m['home_goals'])); self.ag.insert(0,str(m['away_goals']))

    def save_result(self):
        if self.selected_fixture is None: messagebox.showwarning("Select a match","Select a fixture first."); return
        try:
            hg,ag=int(self.hg.get().strip()),int(self.ag.get().strip())
            if hg<0 or ag<0: raise ValueError
        except ValueError: messagebox.showerror("Invalid score","Enter whole numbers of zero or greater."); return
        m=self.fixtures[self.selected_fixture]; m.update(played=True,home_goals=hg,away_goals=ag); self.save_data(); messagebox.showinfo("Saved",f"{m['home']} {hg} - {ag} {m['away']}\nHome ground: {self.teams.get(m['home'],'Stadium not set')}")
        self.show_dashboard("Fixtures & Results")

    def build_teams(self,parent):
        self.team_tree=self.tree(parent,("team","stadium"),("TEAM","HOME STADIUM"),(360,450))
        for team,stadium in self.teams.items(): self.team_tree.insert("","end",values=(team,stadium))
        form=tk.Frame(parent,bg=PANEL,padx=12,pady=12); form.pack(fill="x",pady=8)
        tk.Label(form,text="Team name",bg=PANEL,fg=TEXT).grid(row=0,column=0,sticky="w"); self.team_name=tk.Entry(form,width=25); self.team_name.grid(row=1,column=0,padx=(0,12))
        tk.Label(form,text="Home stadium",bg=PANEL,fg=TEXT).grid(row=0,column=1,sticky="w"); self.stadium_name=tk.Entry(form,width=30); self.stadium_name.grid(row=1,column=1,padx=(0,12))
        self.button(form,"ADD TEAM",self.add_team,green=True).grid(row=1,column=2)
        tk.Label(parent,text="Stadiums are displayed for every home fixture. Adding teams after fixtures exist requires creating a new league to regenerate a complete schedule.",bg=BG,fg=MUTED,wraplength=850,justify="left").pack(anchor="w",pady=8)

    def add_team(self):
        name=self.team_name.get().strip(); stadium=self.stadium_name.get().strip()
        if not name or not stadium: messagebox.showerror("Required","Enter both a team name and stadium."); return
        if name.casefold() in {x.casefold() for x in self.teams}: messagebox.showerror("Duplicate","That team already exists."); return
        self.teams[name]=stadium; self.save_data(); self.show_dashboard("Teams & Stadiums")

    def build_history(self,parent):
        played=[m for m in self.fixtures if m.get('played')]
        tk.Label(parent,text="COMPETITION RECORD",bg=BG,fg=TEXT,font=("Segoe UI",14,"bold")).pack(anchor="w",pady=(0,8))
        stats=calculate_table(list(self.teams),self.fixtures)
        cards=tk.Frame(parent,bg=BG); cards.pack(fill="x")
        for title,value,hint in [("Matches completed",str(len(played)),"Results stored"),("Goals scored",str(sum(stats[t]['GF'] for t in self.teams)),"Across this competition"),("Draws",str(sum(stats[t]['D'] for t in self.teams)//2),"Level scores")]: self.card(cards,title,value,hint).pack(side="left",fill="x",expand=True,padx=(0,10))
        tk.Label(parent,text="RESULT ARCHIVE",bg=BG,fg=TEXT,font=("Segoe UI",13,"bold")).pack(anchor="w",pady=(22,4))
        t=self.tree(parent,("week","home","score","away","stadium"),("WEEK","HOME TEAM","SCORE","AWAY TEAM","HOME STADIUM"),(100,220,100,220,260))
        for m in played: t.insert("","end",values=(f"{m.get('leg', 'First Leg')} • Week {m.get('week',1)}",m['home'],f"{m['home_goals']} - {m['away_goals']}",m['away'],self.teams.get(m['home'],'Stadium not set')))
        if self.fixtures and len(played)==len(self.fixtures):
            champ=self.ranked()[0]; tk.Label(parent,text=f"🏆 CHAMPIONS: {champ}  •  {self.teams.get(champ,'')}",bg=PANEL,fg=GREEN,font=("Segoe UI",15,"bold"),padx=14,pady=12).pack(fill="x",pady=12)


def main():
    root=tk.Tk(); PremierLeagueApp(root); root.mainloop()

if __name__ == '__main__': main()
