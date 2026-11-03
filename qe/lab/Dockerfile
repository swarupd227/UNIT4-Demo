# The test lab: the billing module built as it is and once per seeded fault, plus Playwright.
# A run starts one build on a fresh copy of the seeded database, runs tests against it and stops it.

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-yaml && rm -rf /var/lib/apt/lists/*
WORKDIR /work
COPY qe/estate/src/Billing.Web/Billing.Web.csproj src/Billing.Web/
RUN dotnet restore src/Billing.Web/Billing.Web.csproj
COPY qe/estate/src src
RUN find src -type d \( -name bin -o -name obj \) -prune -exec rm -rf {} + && dotnet restore src/Billing.Web/Billing.Web.csproj
COPY qe/faults faults
COPY qe/lab/build_variants.py .
RUN python3 build_variants.py
# The seeded test database, made once by the baseline build. Every run starts from a copy.
RUN mkdir -p /seed && dotnet /builds/baseline/Billing.Web.dll --seed-only=true --Billing:Database=/seed/billing.db

FROM mcr.microsoft.com/playwright:v1.49.1-noble
RUN apt-get update && apt-get install -y --no-install-recommends aspnetcore-runtime-8.0 && rm -rf /var/lib/apt/lists/*
WORKDIR /lab
COPY qe/estate/tests/e2e/package.json tests/package.json
RUN cd tests && npm install --no-audit --no-fund --silent
COPY --from=build /builds /builds
COPY --from=build /seed /seed
COPY qe/lab/run.mjs .
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1
ENTRYPOINT ["node", "/lab/run.mjs"]
