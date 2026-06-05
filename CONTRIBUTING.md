# Доприношење — начин рада (ways of working)

Канонска правила развојног тока за **spc-registar**. README даје кратак преглед; овде су детаљи.

## Гранање

Гранај од `main`. Префикс гране одређује како се верзија подиже при мерџу (види [Верзионисање](#верзионисање)):

| Префикс | Бамп | За шта |
|---|---|---|
| `feature/`, `feat/` | **minor** | нова функционалност |
| `fix/`, `bugfix/`, `hotfix/` | **patch** | исправке грешака |
| `perf/`, `refactor/`, `chore/`, `docs/`, `build/`, `ci/`, `test/`, `style/` | **patch** | одржавање, перформансе, документација, алат |

- Препоручено именовање: `feature/<кратки-опис>` или `fix/<број-issue>-<опис>` (нпр. `fix/256-context-processor`).
- Грана **`bug`**-означеног issue-а иде у `fix/`; функционалност/`enhancement` у `feature/`.
- **Сваки други префикс ће оборити auto-tag** при мерџу (намерно — да се погрешно име не превиди). Не комитуј директно на `main`.

## Верзионисање

`.github/workflows/auto-tag.yml` подиже семвер таг при сваком мерџу PR-а у `main`, на основу префикса гране (табела горе). Непознат префикс **обара** job (нема тихог прескакања). Основа је најновији `X.Y.Z` таг достижан са `main`; за major бамп, поставите таг ручно једном.

## Поруке комита

Conventional Commits (проверава `conventional-pre-commit`):

```
<тип>(<опсег>): <опис>
```

Дозвољени типови: `feat fix refactor docs test chore ci perf style build revert`. Без `Co-authored-by:` трејлера (хук `no-coauthored-by` га одбија).

## pre-commit

Инсталирај једном, па ради аутоматски:

```
pre-commit install                       # активира git хукове (pre-commit + commit-msg)
pre-commit run --files <измењени фајлови> # ручно пре пуша
```

Хук `branch-name` проверава конвенцију именовања гране (једнократно заобиђи са `ALLOW_BRANCH=1 git commit ...`). Остали хукови: ruff, isort, autoflake, pylint, biome (CSS/JS), djlint (темплејти), Django тестови.

## Тестови

```
python crkva/manage.py test registar.tests tenants.tests kalendar.tests --parallel 1
```

Покрећи из корена репозиторијума (неки тестови читају статичке фајлове релативно на радни директоријум). Више: [docs/testing.md](docs/testing.md).

## Pull Request

1. Направи грану по конвенцији.
2. `pre-commit run --files <измењени>` и тестови зелени.
3. Отвори PR на `main`. При мерџу `auto-tag` подиже верзију.
