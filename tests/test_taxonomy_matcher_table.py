"""Table-driven test suite with >= 100 test cases for BoundarySafeMatcher."""

import pytest

from careercompiler.taxonomy.normalizer import get_default_normalizer

normalizer = get_default_normalizer()


# ---------------------------------------------------------------------------
# Table of >= 100 test cases: (input_text, expected_canonical_ids)
# ---------------------------------------------------------------------------
TEST_CASES = [
    # --- 1. Java vs JavaScript (Spec Requirement) ---
    ("Looking for Java and JavaScript developers.", ["java", "javascript"]),
    ("Pure Java backend service architecture.", ["java"]),
    ("Vanilla JavaScript in modern frontend.", ["javascript"]),
    ("Modern JavaScript and TypeScript frameworks.", ["javascript", "typescript"]),
    ("Enterprise applications running on Java 17 JDK.", ["java"]),
    ("Writing asynchronous JavaScript with ES6 features.", ["javascript"]),
    ("Senior Java engineer leading backend microservices.", ["java", "microservices"]),
    ("Migrated legacy Java monolith to microservices.", ["java", "microservices"]),
    ("JavaScript engineer with DOM experience.", ["javascript"]),
    ("Client-side scripting in ECMAScript and JavaScript.", ["javascript"]),

    # --- 2. C vs C++ vs C# (Spec Requirement) ---
    ("Proficient in C++ and C#.", ["cpp", "csharp"]),
    ("Low level systems programming in C.", ["c"]),
    ("C/C++ development experience.", ["c", "cpp"]),
    ("Modern C++20 and C++17 standards.", ["cpp"]),
    ("Developed desktop tools using C# and .NET.", ["csharp", "dotnet"]),
    ("Firmware driver developed in C for ARM.", ["c"]),
    ("Embedded systems engineer using C and Assembly.", ["c", "assembly"]),
    ("Writing native extensions in C++.", ["cpp"]),
    ("Enterprise backend in C# on ASP.NET Core.", ["csharp", "aspnet"]),
    ("Meeting held in conference room C.", []),
    ("Executive C suite leadership discussion.", []),
    ("Student received a Grade C in economics.", []),
    ("Refer to section C of the document.", []),
    ("Figure C displays the architecture diagram.", []),

    # --- 3. Go language vs Verb (Spec Requirement) ---
    ("Seeking a senior Go developer.", ["golang"]),
    ("Microservices written in Go and Python.", ["golang", "python", "microservices"]),
    ("Skills: Go/Python/Rust", ["golang", "python", "rust"]),
    ("Deep experience with Golang concurrency.", ["golang", "concurrency"]),
    ("Experience in Go, Java, and C++.", ["golang", "java", "cpp"]),
    ("High throughput backend built in Go.", ["golang"]),
    ("Let's go to the cafeteria.", []),
    ("We should go ahead with the proposal.", []),
    ("Always on the go during travel.", []),
    ("Give it a go tomorrow morning.", []),
    ("Where did you go yesterday?", []),
    ("Go live date is next Monday.", []),
    ("Things will go smoothly from here.", []),
    ("Please go over the release notes.", []),

    # --- 4. R language vs R&D (Spec Requirement) ---
    ("Data analysis using R and Python.", ["r", "python"]),
    ("Experience in R for statistical modeling.", ["r"]),
    ("R programming and ggplot libraries.", ["r"]),
    ("Biostatistics workflows in RStudio and R.", ["r"]),
    ("Leading the corporate R&D initiatives.", []),
    ("Collaboration between R & D teams.", []),
    ("Appendix R contains additional notes.", []),
    ("Budget allocated for R&D operations.", []),

    # --- 5. .NET and Dot Handling (Spec Requirement) ---
    ("Enterprise microservices built on .NET 8.", ["dotnet", "microservices"]),
    ("C# and .NET Framework architecture.", ["csharp", "dotnet"]),
    ("Modern cloud apps with ASP.NET Core.", ["aspnet"]),
    ("Developed backend with .NET Core and SQL Server.", ["dotnet", "mssql"]),
    ("Visit our site at domain.net for info.", []),
    ("File saved as document.net in storage.", []),

    # --- 6. Node.js / NodeJS (Spec Requirement) ---
    ("Full stack development with Node.js and React.", ["nodejs", "react"]),
    ("Built REST APIs using NodeJS and Express.", ["rest-api", "nodejs", "express"]),
    ("Backend runtime on node.js with TypeScript.", ["nodejs", "typescript"]),
    ("Traversed 500 nodes in the distributed graph.", []),
    ("Compute cluster consisting of 16 worker nodes.", []),

    # --- 7. Next.js / NextJS (Spec Requirement) ---
    ("Server side rendering using Next.js framework.", ["nextjs"]),
    ("Frontend migrated to NextJS 14.", ["nextjs"]),
    ("Modern web apps using Next.js and Tailwind CSS.", ["nextjs", "tailwind-css"]),
    ("In the next quarter we will scale.", []),
    ("Moving on to the next topic.", []),

    # --- 8. React vs React Native vs Reactive (Spec Requirement) ---
    ("UI engineered with React and Redux.", ["react"]),
    ("Single-page apps using React.js and TypeScript.", ["react", "typescript"]),
    ("Mobile apps built using React Native.", ["react-native"]),
    ("Cross-platform mobile using ReactNative and Expo.", ["react-native"]),
    ("Reactive programming patterns with RxJava.", []),
    ("Reactor core temperature control system.", []),
    ("Chemical reactor monitoring software.", []),

    # --- 9. Kubernetes vs K8s (Spec Requirement) ---
    ("Orchestrated container workloads using Kubernetes.", ["kubernetes"]),
    ("Managed production K8s clusters.", ["kubernetes"]),
    ("Automated deployments on k8s with Helm.", ["kubernetes", "helm"]),
    ("Cloud native infrastructure managed by Kubernetes.", ["kubernetes"]),

    # --- 10. PostgreSQL vs Postgres vs psql (Spec Requirement) ---
    ("Relational queries optimized in Postgres.", ["postgresql"]),
    ("High availability clustering with PostgreSQL.", ["postgresql"]),
    ("Administered databases via psql CLI.", ["postgresql"]),
    ("PostgreSQL database migrations using Flyway.", ["postgresql"]),

    # --- 11. Docker vs Docker Compose ---
    ("Containerized applications using Docker.", ["docker"]),
    ("Local multi-service dev environment via Docker Compose.", ["docker-compose"]),
    ("Wrote multi-stage Dockerfile for production.", ["docker"]),

    # --- 12. PyTorch vs PyTorch Geometric ---
    ("Deep learning research using PyTorch.", ["pytorch"]),
    ("Graph neural network in PyTorch Geometric.", ["gnn", "pytorch-geometric"]),
    ("Trained computer vision models in PyTorch.", ["pytorch"]),

    # --- 13. Rust vs Trust / Words ---
    ("Memory safe systems written in Rust.", ["rust"]),
    ("Rust developer with experience in Cargo.", ["rust"]),
    ("High performance networking in Rust and C++.", ["rust", "cpp"]),
    ("Building customer trust through transparency.", []),
    ("The ancient iron bridge had rusted away.", []),
    ("Working in the Rust Belt region.", []),
    ("Crust of the bread was baked well.", []),

    # --- 14. Apache Spark vs Spark ---
    ("Big data ETL pipelines using Apache Spark and Hadoop.", ["apache-spark"]),
    ("Distributed computations with PySpark.", ["apache-spark"]),
    ("Spark streaming jobs for real-time telemetry.", ["apache-spark"]),
    ("A spark of creativity can ignite great ideas.", []),
    ("The electrical short caused a dangerous spark.", []),
    ("Bright spark student in the classroom.", []),

    # --- 15. REST vs Rest of Team ---
    ("Architected RESTful APIs with OpenAPI specs.", ["rest-api"]),
    ("Designing scalable REST API endpoints.", ["rest-api"]),
    ("Take a well-deserved rest over the weekend.", []),
    ("The rest of the team will join later.", []),
    ("Rest of the data was discarded.", []),

    # --- 16. CI/CD & DevOps Practices ---
    ("Automated testing in CI/CD pipelines.", ["ci-cd"]),
    ("Configured continuous integration and CI / CD.", ["ci-cd"]),
    ("GitLab CI/CD automated deployment workflow.", ["gitlab-ci"]),
    ("GitHub Actions workflows for automated CI/CD.", ["github-actions", "ci-cd"]),

    # --- 17. Cloud Platforms & Services ---
    ("Deployed serverless functions on AWS Lambda.", ["aws-lambda"]),
    ("Object storage using Amazon S3 buckets.", ["aws-s3"]),
    ("Infrastructure on Google Cloud Platform (GCP).", ["gcp"]),
    ("Multi-region cloud failover in Azure.", ["azure"]),
    ("Relational database hosting on Amazon RDS.", ["aws-rds"]),
    ("Message broker configured with Amazon SQS and SNS.", ["aws-sqs", "aws-sns"]),

    # --- 18. Punctuation, Slashes, and Bracket Boundaries ---
    ("Languages: [Python, TypeScript, SQL]", ["python", "typescript", "sql"]),
    ("Backend stack: (FastAPI/Celery/Redis)", ["fastapi", "celery", "redis"]),
    ("Database: \\textbf{PostgreSQL} engine", ["postgresql"]),
    ("Dependencies: 'Docker', 'Kubernetes'", ["docker", "kubernetes"]),
    ("Tech: Python/Go/Rust", ["python", "golang", "rust"]),

    # --- 19. Authentic Bullets from Resume Template ---
    (
        "Architected modular end-to-end and REST API test frameworks using Playwright and OOP design patterns.",
        ["rest-api", "playwright", "oop"],
    ),
    (
        "Architected an asynchronous, distributed backend microservice with FastAPI, Celery, and Redis as a message broker.",
        ["fastapi", "celery", "redis", "microservices"],
    ),
    (
        "Architected a multi-task Graph Convolutional Network (GCN) in PyTorch Geometric across 13,753 clinical isolates.",
        ["gcn", "pytorch-geometric"],
    ),
    (
        "Engineered Agentic AI workflows and structured prompt optimization pipelines within CI/CD.",
        ["agentic-ai", "prompt-engineering", "ci-cd"],
    ),
    (
        "Deploying to Qdrant vector database and Redis cache with Docker Compose.",
        ["qdrant", "redis", "docker-compose"],
    ),

    # --- 20. Negative Substring Invariant Cases ---
    ("Creating an innovative algorithmic solution.", ["algorithms"]),
    ("Developed backend services in Django.", ["django"]),
    ("Data stored in MongoDB collections.", ["mongodb"]),
    ("Understanding general concept of scalability.", []),
    ("Handling large scale production traffic.", []),
    ("High performance computing architecture.", []),
    ("Sprint schedule and planning meeting.", []),
    ("Automated regression testing suite.", []),
    ("Building robust microservices for clients.", ["microservices"]),
    ("Comprehensive documentation of software features.", []),
]


def test_table_cases_count() -> None:
    """Verify test table has >= 100 test cases as required by spec."""
    assert len(TEST_CASES) >= 100, f"Expected >= 100 cases, found {len(TEST_CASES)}"


@pytest.mark.parametrize("text,expected_ids", TEST_CASES)
def test_boundary_safe_matcher_table(text: str, expected_ids: list[str]) -> None:
    matches = normalizer.normalize(text)
    matched_ids = [m.canonical_id for m in matches]

    # Check set equivalence (ignoring order or duplicates)
    assert set(matched_ids) == set(expected_ids), (
        f"\nText: {text}\n"
        f"Expected canonical IDs: {expected_ids}\n"
        f"Actual matched IDs:   {matched_ids}\n"
        f"Matches detail:        {[(m.canonical_id, m.surface_form, m.start, m.end) for m in matches]}"
    )
