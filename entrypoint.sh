#!/usr/bin/env bash

case ${1} in
  health-monitor-backend)
    cd "$PYTHONPATH" || exit 100
    uvicorn app.main:app --host 0.0.0.0 --port 8000 || exit $?
    ;;

  database-migrations)
    cd "$PYTHONPATH" || exit 100
    if [ "$DATABASE_ALEMBIC_MIGRATION_ROLLBACK" = "true" ]; then
      alembic downgrade "$DATABASE_ALEMBIC_MIGRATION_REVISION" || exit $?
    else
      alembic upgrade head || exit $?
      alembic check || exit $?
    fi
    ;;

  *)
    exit 104
    ;;
esac
