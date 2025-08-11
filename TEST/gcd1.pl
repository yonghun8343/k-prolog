gray(1,['0','1']).
gray(N,C) :- N > 1, N1 is N-1,
   gray(N1,C1), reverse(C1,C2),
   prepend('0',C1,C1P),
   prepend('1',C2,C2P),
   append(C1P,C2P,C).

prepend(_,[],[]) :- !.
prepend(X,[C|Cs],[CP|CPs]) :- atom_concat(X,C,CP), prepend(X,Cs,CPs).