# HelixLAB engine sandbox (spec §7).
# Runtime contract (enforced by the worker at `docker run` time):
#   --network none            # no network access, ever
#   --memory 2g --cpus 2      # cgroup limits
#   --read-only               # writes confined to /tmp volume
#   --cap-drop ALL            # no privileges
# Engine base images (wolfram-engine, gap, sage, qiskit) are layered on this
# in sprint 1; versions pinned per spec §13.2 (unresolved).
FROM python:3.12-slim

RUN useradd --create-home --shell /usr/sbin/nologin sandbox
USER sandbox
WORKDIR /tmp/work

# No engine binaries in the base sandbox: each engine gets its own image
# FROM this one. Nothing else is installed by design.
CMD ["sleep", "infinity"]