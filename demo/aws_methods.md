# AWS Methods

### 1. AOI bucket with static Foundation - &check;

```mermaid
flowchart LR
    id1["AOI <br> bucket"]--trigger-->lambda
    id2["FND <br> bucket"]-->lambda
    lambda-->S3_RST["result <br> bucket"]
```

<br/><br/>

### 2. AOI bucket with step function and dynamic Foundation - &check;

```mermaid
flowchart LR
    subgraph id0["step function"]
        direction LR
        id1["lambda <br> dynamic FND"] --> id2["lambda <br> coregister"]
    end
    id3["AOI <br> bucket"]--event-->id0
    id0-->id4["result <br> bucket"]
    id5["PC 3DEP"]-->id0
```

<br/><br/>

### 3. AOI bucket and API feeding a queue - Under construction

```mermaid
flowchart LR
    id1["AOI <br> bucket"]--event-->SQS
    id1-->lambda
    id2["API"]--POST-->SQS
    SQS--trigger-->lambda
    lambda-->id3["result <br> bucket"]
    id4["PC 3DEP"]-->lambda
```

<br/><br/>

### 4. Cirrus?
