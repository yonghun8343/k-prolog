# k-prolog

## Clone 이후 해야할 작업

poetry를 우선 설치

project clone 후

``` shell
poetry install --no-root
```

## Gitflow 적용 방법

### Branch 생성

``` shell
git branch [branch 이름(작업 이름))]
ex) git branch add_poetry
```

### Branch 생성 후 해당 Branch로 이동

``` shell
git checkout [생성한 branch 이름]
ex) git checkout add_poetry
```

### 작업 완료 후 Push

``` shell
git add .
git commit -m 