
father(john, jim).
father(jack, john).
father(adam, jane).
father(louis, alan).
father(bob, chris).
father(alan, mike).
father(alan, joan).

mother(mary, john).
mother(eve, jane).
mother(violet, bob).
mother(jane, jim).


parent(X, Y) :- father(X, Y).
parent(X, Y) :- mother(X, Y).

child(Y, X) :- parent(X, Y).

grandParent(X, Z) :-
    parent(X, Y),
    parent(Y, Z).


main :-
    read(Name),
    findall(C, child(C, Name), Children),
    ( Children = [] ->
        writeln(none)
    ;
        print_list(Children)
    ),
    halt.

:- initialization(main).


print_list([]).
print_list([H|T]) :-
    writeln(H),
    print_list(T).