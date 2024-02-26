import React, { useState, useEffect } from 'react';

const DevConsole = () => {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const log = console.log;
    const error = console.error;

    console.log = (...args) => {
      setLogs((prevLogs) => [...prevLogs, { type: 'log', message: args.join(' ') }]);
      log(...args);
    };

    console.error = (...args) => {
      setLogs((prevLogs) => [...prevLogs, { type: 'error', message: args.join(' ') }]);
      error(...args);
    };

    return () => {
      console.log = log;
      console.error = error;
    };
  }, []);

  return (
    <div className="dev-console">
      {logs.map((log, index) => (
        <div key={index} className={`log-entry ${log.type}`}>
          {log.message}
        </div>
      ))}
    </div>
  );
};

export default DevConsole;
