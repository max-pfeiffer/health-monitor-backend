#!/usr/bin/env bash

case ${1} in
  health-monitor-backend)
    cd "$PYTHONPATH" || return 100
    uvicorn app.main:app --host 0.0.0.0 --port 8000 || return $?
    ;;

  database-migrations)
    cd "$PYTHONPATH" || return 100
    if [ "$DATABASE_ALEMBIC_MIGRATION_ROLLBACK" = "true" ]; then
      alembic downgrade "$DATABASE_ALEMBIC_MIGRATION_REVISION" || return $?
    else
      alembic upgrade head || return $?
      alembic check || return $?
    fi
    ;;

  *)
    return 104
    ;;
esac
