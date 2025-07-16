enjoys(vincent,X):- bigKahunaBurger(X), !, fail.
enjoys(vincent,X):- burger(X).
burger(X):- bigMac(X).
burger(X):- bigKahunaBurger(X).
burger(X):- whopper(X).
bigMac(a).
bigKahunaBurger(b).
bigMac(c).
whopper(d).