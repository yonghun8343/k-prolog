natnum(0).
natnum(s(N)) :-
        natnum(N).
    

nat_nat_sum(0, M, M).
nat_nat_sum(s(N), M, s(Sum)) :-
        nat_nat_sum(M, N, Sum).
    


list_length([], 0).
list_length([_|Ls], Length) :-
        Length #= Length0 + 1,
        list_length(Ls, Length0).
    


list_length(Ls, L) :-
        list_length_(Ls, 0, L).

list_length_([], L, L).
list_length_([_|Ls], L0, L) :-
        L1 #= L0 + 1,
        list_length_(Ls, L1, L).
    
split(L,0,[],L).
split([X|Xs],N,[X|Ys],Zs) :- N > 0, N1 is N - 1, split(Xs,N1,Ys,Zs).

lsort(InList,OutList) :- lsort(InList,OutList,asc).


lsort(InList,OutList,Dir) :-
   add_key(InList,KList,Dir),
   write(InList),
   keysort(KList,SKList),
   rem_key(SKList,OutList).

add_key([],[],_).
add_key([X|Xs],[L-p(X)|Ys],asc) :- !, 
        length(X,L), add_key(Xs,Ys,asc).
add_key([X|Xs],[L-p(X)|Ys],desc) :- 
        length(X,L1), L is -L1, add_key(Xs,Ys,desc).

rem_key([],[]).
rem_key([_-p(X)|Xs],[X|Ys]) :- rem_key(Xs,Ys).