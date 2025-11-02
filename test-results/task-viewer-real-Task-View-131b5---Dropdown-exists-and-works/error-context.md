# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - link "Skip to main content" [ref=e2] [cursor=pointer]:
    - /url: "#main-content"
  - generic [ref=e3]:
    - banner [ref=e4]:
      - generic [ref=e6]:
        - heading "Task Viewer" [level=1] [ref=e8]
        - button "Select Project" [ref=e11] [cursor=pointer]:
          - generic [ref=e12]: Select Project
          - img [ref=e13]
        - button "API Key Configured" [ref=e16] [cursor=pointer]:
          - img [ref=e17]
    - generic [ref=e20]:
      - generic [ref=e21]:
        - generic [ref=e22]: "Status:"
        - button "All (0)" [pressed] [ref=e23] [cursor=pointer]
        - button "Todo (0)" [ref=e24] [cursor=pointer]
        - button "In Progress (0)" [ref=e25] [cursor=pointer]
        - button "Done (0)" [ref=e26] [cursor=pointer]
        - button "Blocked (0)" [ref=e27] [cursor=pointer]
      - generic [ref=e28]:
        - textbox "Search tasks" [ref=e30]:
          - /placeholder: Search tasks...
        - 'button "Priority: All" [ref=e32] [cursor=pointer]'
        - button "Sort" [ref=e34] [cursor=pointer]
    - main [ref=e35]:
      - status [ref=e36]: Showing 0 of 0 tasks
      - generic [ref=e38]:
        - img [ref=e39]
        - generic [ref=e41]:
          - heading "Error loading tasks" [level=3] [ref=e42]
          - paragraph [ref=e43]: Invalid API key. Please check your configuration.
          - button "Retry" [ref=e44] [cursor=pointer]
```