% Example
% ?- huffman([fr(a,45),fr(b,13),fr(c,12),fr(d,16),fr(e,9),fr(f,5)],C).
% C = [hc(a,'0'),hc(b,'101'),hc(c,'100'),hc(d,'111'),hc(e,'1101'),hc(f,'1100')]+

% During the construction process, we need nodes n(F,S) where, at the 
% beginning, F is a frequency and S a symbol. During the process, as n(F,S)
% becomes an internal node, S becomes a term s(L,R) with L and R being 
% again n(F,S) terms. A list of n(F,S) terms, called Ns, is maintained 
% as a sort of priority queue.

huffman(Fs,Cs) :-
   initialize(Fs,Ns),write(Ns),
   make_tree(Ns,T),write("writing tree"), write(T),
   traverse_tree(T,Cs).

initialize(Fs,Ns) :- init(Fs,NsU), sort(NsU,Ns).

init([],[]).
init([fr(S,F)|Fs],[n(F,S)|Ns]) :- init(Fs,Ns).

make_tree([T],T).
make_tree([n(F1,X1),n(F2,X2)|Ns],T) :- 
   F is F1+F2,
   insert(n(F,s(n(F1,X1),n(F2,X2))),Ns,NsR),
   make_tree(NsR,T).

insert(N,[],[N]) :- !.
insert(n(F,X),[n(F0,Y)|Ns],[n(F,X),n(F0,Y)|Ns]) :- F < F0, !.
insert(n(F,X),[n(F0,Y)|Ns],[n(F0,Y)|Ns1]) :- F >= F0, insert(n(F,X),Ns,Ns1).


traverse_tree(T,Cs) :- write("meep"), traverse_tree(T,'',Cs1-[]), sort(Cs1,Cs).

traverse_tree(n(_,A),Code,[hc(A,Code)|Cs]-Cs) :- atom(A).
traverse_tree(n(_,s(Left,Right)),Code,Cs1-Cs3) :-
   atom_concat(Code,'0',CodeLeft), 
   atom_concat(Code,'1',CodeRight),
   traverse_tree(Left,CodeLeft,Cs1-Cs2),
   traverse_tree(Right,CodeRight,Cs2-Cs3).