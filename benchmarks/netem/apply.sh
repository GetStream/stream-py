#!/usr/bin/env bash
# Apply a tc/netem impairment profile on the default (or given) Linux iface.
# Run later on the canonical bench host as root. Does not shape Docker Desktop.
#
# Usage:
#   sudo benchmarks/netem/apply.sh <clean|loss-1pct|loss-5pct|cap-1mbps|rtt-200ms> [iface]
#   IFACE=eth0 sudo benchmarks/netem/apply.sh loss-1pct
set -euo pipefail

PROFILE="${1:-}"
if [[ -z "$PROFILE" ]]; then
  echo "usage: $0 <clean|loss-1pct|loss-5pct|cap-1mbps|rtt-200ms> [iface]" >&2
  exit 2
fi

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "netem profiles require Linux tc/netem; this host is $(uname -s)" >&2
  exit 1
fi

if [[ "${EUID}" -ne 0 ]]; then
  echo "tc qdisc changes require root (rerun with sudo)" >&2
  exit 1
fi

IFACE="${2:-${IFACE:-}}"
if [[ -z "$IFACE" ]]; then
  IFACE="$(ip -o route show default 2>/dev/null | awk '{print $5; exit}')"
fi
if [[ -z "$IFACE" ]]; then
  echo "could not detect default iface; pass it as argv2 or IFACE=" >&2
  exit 1
fi

tc qdisc del dev "$IFACE" root 2>/dev/null || true

case "$PROFILE" in
  clean)
    echo "cleared qdisc on $IFACE"
    ;;
  loss-1pct)
    tc qdisc add dev "$IFACE" root netem loss 1%
    echo "applied 1% loss on $IFACE"
    ;;
  loss-5pct)
    tc qdisc add dev "$IFACE" root netem loss 5%
    echo "applied 5% loss on $IFACE"
    ;;
  cap-1mbps)
    tc qdisc add dev "$IFACE" root tbf rate 1mbit burst 32kbit latency 50ms
    echo "applied 1mbit cap on $IFACE"
    ;;
  rtt-200ms)
    # Egress delay only; +200ms one-way ≈ +200ms RTT against an unshaped return path.
    tc qdisc add dev "$IFACE" root netem delay 200ms
    echo "applied 200ms egress delay on $IFACE"
    ;;
  *)
    echo "unknown profile: $PROFILE" >&2
    exit 2
    ;;
esac

tc qdisc show dev "$IFACE"
