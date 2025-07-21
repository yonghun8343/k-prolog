gcd(X, 0, X) :- X > 0.
gcd(X, Y, G) :-
    Y > 0,
    (X < Y ->
        gcd(Y, X, G)
    ;
        D is X - Y,
        gcd(Y, D, G)).

lcm(X, Y, L) :-
    gcd(X, Y, G),
    P is X * Y,
    L is P // G.

main :-
    read(X),
    read(Y),
    gcd(X, Y, G),
    writeln(G),
    lcm(X, Y, L),
    writeln(L),
    halt.

:- initialization(main).
