is_prime(2).
is_prime(3).
is_prime(P) :- integer(P), P > 3, R is P mod 2, R =\= 0, not(has_factor(P,3)).

has_factor(N,L) :- R is N mod L, R =:= 0.
has_factor(N,L) :- L * L < N, L2 is L + 2, has_factor(N,L2).

goldbach(4,[2,2]) :- !.
goldbach(N,L) :- R is N mod 2, R =:= 0, N > 4, goldbach(N,L,3).

goldbach(N,[P,Q],P) :- Q is N - P, is_prime(Q), !.
goldbach(N,L,P) :- P < N, next_prime(P,P1), goldbach(N,L,P1).

next_prime(P,P1) :- P1 is P + 2, is_prime(P1), !.
next_prime(P,P1) :- P2 is P + 2, next_prime(P2,P1).

prime_list(A,B,L) :- A =< 2, !, p_list(2,B,L).
prime_list(A,B,L) :- A1 is (A // 2) * 2 + 1, p_list(A1,B,L).

p_list(A,B,[]) :- A > B, !.
p_list(A,B,[A|L]) :- is_prime(A), !, next(A,A1), p_list(A1,B,L). 
p_list(A,B,L) :- next(A,A1), p_list(A1,B,L).

next(2,3) :- !.
next(A,A1) :- A1 is A + 2.