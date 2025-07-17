queens(N,Qs) :- 
    range(1,N,Ns), permutation(Ns,Qs), safe(Qs).

safe([]).
safe([Q|Qs]) :- safe(Qs), not(attack(Q,Qs)).

attack(X,Xs) :- attack(X,1,Xs).
attack(X,N,[Y|_]) :- X is Y+N; X is Y-N.
attack(X,N,[_|Ys]) :- N1 is N+1, attack(X,N1,Ys).

range(N,N,[N]).
range(M,N,[M|Ns]) :- M < N, M1 is M+1, range(M1,N,Ns).