## Methods

1. AOI bucket trigger: static Foundation

    ```mermaid
    flowchart LR
        S3_AOI["AOI <br> Bucket"] -- trigger --> lambda
        S3_FND["FND <br> Bucket"] --> lambda
        lambda --> S3_RST["Result <br> Bucket"]
    ```

2. AOI bucket trigger: dynamic Foundation

```mermaid
flowchart LR
    subgraph id0["step function"]
        direction LR
        id1["lambda <br> 3DEP FND"] --> id2["lambda <br> coregister"]
    end
    id3["AOI <br> Bucket"] -- event --> id0
    id4["PC 3DEP"] --> id1
    id2 --> id5["Result <br> Bucket"]
```

3. Queue feeders:
    - Bucket create event
    - API POST

```mermaid
flowchart LR
    S3_AOI["AOI <br> Bucket"]-- event -->SQS
    API["API"]-- POST -->SQS
    SQS-->lambda
    lambda-->S3_RESULT["Result <br> Bucket"]
```
