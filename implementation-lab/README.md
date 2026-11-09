# MSS Ltd implementation verification

The coursework brief calls for cross-department data access and a backup database. The Packet Tracer model describes the network and service placement. This companion lab verifies SQL access and restoration with PostgreSQL and synthetic records.

## Reproduce the database test

Run from the repository root with Docker Engine or Docker Desktop. The runner uses a cached image, creates two internal networks and disposable database containers, and removes its resources at exit. It publishes no host ports.

```sh
docker pull postgres:16-alpine
./implementation-lab/verify-database.sh ./implementation-lab/evidence/database-rerun.txt
```

The test creates one record per department in separate schemas, reads all three as the application role, confirms that the role cannot delete a sales record, and streams a custom-format dump into an isolated restore instance. It compares all restored records to the expected values. The operator uses the Docker control plane to transfer the dump. The test covers data integrity and access privileges for the sample workload. Production backup transport, scheduled archive retention and recovery time objectives require deployment tests.

See [the recorded run](evidence/database-verification.txt).
