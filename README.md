# k-prolog

## Clone 이후 해야할 작업

poetry를 우선 설치

project clone 후

``` shell
poetry env use python
poetry install --no-root --with lint
poetry config virtualenvs.in-project true
```

## Gitflow 적용 방법

### Branch 생성

``` shell
git branch [branch 이름(작업 이름))]
ex) git branch add_poetry
ex) git branch setting/add_poetry
ex) git branch feature/is_operation
```

### Branch 생성 후 해당 Branch로 이동

```bash
git checkout [생성한 branch 이름]
ex) git checkout add_poetry
```

### 작업 완료 후 Push

```bash
git add . 
or 
git add *

git commit -m "[변경 내용]"
ex) git commit -m "add poetry settings"

git push origin [branch 이름]
```

### PR 생성하는 방법
1. Github로 이동 [누르면 이동](https://github.com/yonghun8343/k-prolog#)
2. `Compare & pull request` 버튼 클릭
3. 제목/설명 작성

    제목 예:  

    ```text
    feat: 한글 기반 Prolog 파서 추가
    ```

    설명 예:  

    ```diff
    - 한글 질의 입력 처리
    - 기존 Term 구조 유지
    - 테스트는 console에서 수동 확인
    ```
4. Reviewers, Assignees, Label 항목 지정
5. `Create Pull Request` 클릭

### merge(머지)가 완료된 후 로컬 정리

```bash
git checkout main
git pull origin main
git branch -d [브랜치 이름]  # 로컬 브랜치 삭제
```
