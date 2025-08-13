:- initialization(run_list).
run_list :-
    empty_list(L0),
    read(Number1),
    append(L0, [Number1], L1),
    read(Number2),
    append(L1, [Number2], L2),
    read(Number3),
    insert_number(Number3, L2, L3),
    read(Char), write(Char), write(L3),
    output_list(Char, L3).

empty_list([]).

insert_number(0, L, NewL) :-
    % 0이면 리스트 0번째에 삽입
    insert_at(L, 0, 0, NewL).
insert_number(Number, L, NewL) :-
    Number \= 0,
    0 is Number mod 2, % 짝수일 때
    insert_at(L, 1, Number, NewL).
insert_number(Number, L, NewL) :-
    Number \= 0,
    1 is Number mod 2, % 홀수일 때
    insert_at(L, 2, Number, NewL).

insert_at(List, 0, Elem, [Elem|List]).
insert_at([H|T], Index, Elem, [H|NewT]) :-
    Index > 0,
    NextIndex is Index - 1,
    insert_at(T, NextIndex, Elem, NewT).

output_list(A, L) :-
    length(L, Len),
    write(Len), nl, !.
output_list(B, L) :-
    nth0(1, L, Elem),
    write(Elem), nl, !.
output_list(C, L) :-
    last(L, Elem),
    write(Elem), nl, !.
