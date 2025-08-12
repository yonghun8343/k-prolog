ipl(T,L) :- ipl(T,0,L).

ipl(t(_,F),D,L) :- D1 is D+1, ipl(F,D1,LF), L is LF+D.

ipl([],_,0).
ipl([T1|Ts],D,L) :- ipl(T1,D,L1), ipl(Ts,D,Ls), L is L1+Ls.