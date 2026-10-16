export function sqliteAdapter(db, onQuery = () => {}) {
  return {
    execute(sql, parameters) {
      const started = performance.now();
      const statement = db.prepare(sql);
      try {
        if (Array.isArray(parameters)) statement.bind(parameters);
        else {
          // Shared builders include values unused by some statements.
          for (const [name, value] of Object.entries(parameters ?? {})) {
            if (statement.getParamIndex(`:${name}`))
              statement.bind(`:${name}`, value);
          }
        }
        const rows = [];
        while (statement.step()) rows.push(statement.get([]));
        rows.fetchall = () => rows;
        rows.fetchone = () => rows[0] ?? null;
        return rows;
      } finally {
        statement.finalize();
        onQuery(performance.now() - started);
      }
    },
  };
}
