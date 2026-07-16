#!/usr/bin/env bash

case ${1} in
  health-monitor-backend)
    cd "$PYTHONPATH" || exit 100
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
    ;;

  database-migrations)
    cd "$PYTHONPATH" || exit 100
    if [ "$DATABASE_ALEMBIC_MIGRATION_ROLLBACK" = "true" ]; then
      exec alembic downgrade "$DATABASE_ALEMBIC_MIGRATION_REVISION"
    else
      alembic upgrade head || exit $?
      exec alembic check
    fi
    ;;

  *)
    exit 104
    ;;
esac
