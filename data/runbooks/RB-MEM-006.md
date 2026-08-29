document_id: RB-MEM-006
version: 1.5
title: Service memory-leak recovery
services: inventory
type: runbook
trust: reviewed
---
# Service memory-leak recovery

Establish monotonic heap growth across garbage-collection cycles and connect the slope to a deployment. Roll back the implicated version, restart one synthetic replica at a time, and verify heap remains below the scenario threshold for three windows.
