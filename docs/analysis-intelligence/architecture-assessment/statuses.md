# Statuses

| Status | Meaning |
| ------ | ------- |
| not_requested | Section integration not invoked |
| disabled | Integration enabled but architecture pack/analysis disabled |
| not_applicable | No supported architectural evidence source |
| insufficient_evidence | Source exists but meaning cannot be established safely |
| succeeded | Useful architecture section assembled |
| partially_succeeded | Useful results remain after provider/rule/conclusion failures |
| failed | No safe architecture section could be assembled |

Zero findings with sufficient evidence is still `succeeded`.
