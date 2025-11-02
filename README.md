# Deploying a SAP MCP server in SAP BTP

## From Zero to MCP: Deploying an SAP MCP Server on SAP BTP

Bringing an MCP server online in SAP BTP Cloud Foundry can feel like stitching together a lot of moving parts: Cloud Foundry, Destinations, OData discovery, and XSUAA. This guide turns the original checklist into a story-driven walkthrough you can follow end to end—without changing the exact steps, commands, or images you already rely on.

---

## Why this setup?

The goal is simple: You will use a BTP Destination for connectivity and XSUAA for OAuth-based access.

---

Source : ([SAP OData to MCP Server running on BTP - SAP Community](https://community.sap.com/t5/technology-blog-posts-by-members/sap-odata-to-mcp-server-running-on-btp/ba-p/14220561))

## Before you begin

You’ll need:

- An SAP backend service reachable on the internet
- A SAP BTP account with Cloud Foundry enabled
- Cloud Foundry CLI, Node.js/npm, and Python 3 installed

---

## 1) Create your SAP BTP subaccount and space

Start in BTP. Create a subaccount that matches your environment and choose any region suitable for your landscape. Then enable the Cloud Foundry environment and create a space to host the app.

[](https://community.sap.com/t5/image/serverpage/image-id/316093i70DB108FB0B9E1A3/image-dimensions/2500?v=v2&px=-1)

### Quick notes

- Pick a name that maps to your environment lifecycle
- Capture your Cloud Foundry API endpoint for later login

---

## 2) Install the Cloud Foundry CLI and activate CF in your subaccount

Install the Cloud Foundry CLI locally. In BTP, activate the Cloud Foundry environment API for the subaccount and create your space. This ensures the CLI commands you’ll run later have a target to deploy to.

---

## 3) Create a Destination to your SAP backend

Next, wire BTP to your backend system using a Destination. This centralizes credentials and keeps them out of code.

Navigate to Connectivity > Destinations and create a new Destination with:

1. From scratch
2. Name: SAP_Services (or another relevant name)
    
    Type: HTTP
    
    Proxy Type: Internet
    
    Url: url_of_the_sap_backend_services
    
    Authentication: BasicAuthentication
    
    User: username_for_accessing_the_backend_services
    
    Password: password_for_accessing_the_backend_services
    
    Save the configurations
    
3. Click the Destination and run “Check connection” to verify setup. A successful result will look like this:

Tip: Whatever name you choose here must match SAP_DESTINATION_NAME in your .env later.

---

## 4) Prepare the project locally

Clone the repository. Copy .env.example to .env and set recommended discovery defaults, then point SAP_DESTINATION_NAME to your Destination.

[](https://community.sap.com/t5/image/serverpage/image-id/316102iD4D8272896CE7F6A/image-size/medium?v=v2&px=400)

```abap
SAP_DESTINATION_NAME=your-own-destination(SAP_Services)

LOG_LEVEL=debug

# OData Service Discovery Configuration Examples
# Method 1: Allow all services (use * or 'true')
ODATA_ALLOW_ALL=false

# Method 2: Specify service patterns (supports glob patterns)
# Comma-separated list of patterns
ODATA_SERVICE_PATTERNS=*TASKPROCESSING*,*BOOK*,*FLIGHT*,*TRAVEL*,*TRVEXP*,*TRAVELAGENCY*,*TRAVELAGENCYSRV*,*TRAVELAPPROVALS*,*TRAVELAPPROVALS_SRV*,*ZBP*,*ZTRANSPORT*,*ZBC_UI_PARAM_E_CDS*

# Method 3: Use JSON array for more complex patterns
# ODATA_SERVICE_PATTERNS=["ZBP*", "ZTRANSPORT*", "/^Z.*_CDS$/"]

# Method 4: Use regex patterns (enclose in forward slashes)
# ODATA_SERVICE_PATTERNS=/^Z(BP|TRANSPORT).*/

# Exclusion patterns (services to exclude even if they match inclusion patterns)
ODATA_EXCLUSION_PATTERNS=*_TEST*,*_TEMP*

# Maximum number of services to discover (prevents system overload)
ODATA_MAX_SERVICES=50

# Discovery mode: 'all', 'whitelist', 'regex'
ODATA_DISCOVERY_MODE=whitelist
```

Guidance:

- Start narrow with allowlists, then expand as needed
- Keep ODATA_MAX_SERVICES reasonable to prevent discovery spikes

---

## 5) Build and deploy to Cloud Foundry

Time to ship. Use the provided npm scripts and the CF CLI target you prepared earlier.

```abap
npm run build:btp
cf login -a <cf api endpoint of BTP>
npm run deploy:btp
```

[](https://community.sap.com/t5/image/serverpage/image-id/316094i1CF5777D5A680E98/image-size/medium?v=v2&px=400)

[](https://community.sap.com/t5/image/serverpage/image-id/316096i26CFA6F286C5C113/image-size/medium?v=v2&px=400)

[](https://community.sap.com/t5/image/serverpage/image-id/316097i56B7FA6E5B4C4BB2/image-size/medium?v=v2&px=400)

When deployment finishes, you’ll see your app listed in the space:

[](https://community.sap.com/t5/image/serverpage/image-id/316098iF73027C5FC035D73/image-size/medium?v=v2&px=400)

Copy the application URL—you’ll use it in your MCP client.

---

## 6) Retrieve an access token from XSUAA

Your MCP client will authenticate using an OAuth token issued by XSUAA.

1. In the BTP account, go to Services > Instances and Subscriptions
2. Open your XSUAA instance (for example, sap-mcp-xsuaa-dev) or the relevant service key
3. Find the service key named mykey and collect:
    - client_id
    - clientsecret
    - url: https://your_url/oauth/token
4. Add the credentials to access_token_[mcp.py](http://mcp.py)
5. Run the script to get a bearer token:
    - python access_token_[mcp.py](http://mcp.py)

[](https://community.sap.com/t5/image/serverpage/image-id/316103iD546256210A8297A/image-size/medium?v=v2&px=400)

---

## 7) Configure your MCP client (e.g., GitHub Copilot)

With your application URL and access token in hand, configure the client:

- MCP Server URL: the application URL from your deployed app
- Authorization: Bearer <your access token>

That’s it—your MCP client can now talk to the server hosted on BTP, subject to the OData service discovery rules you set in .env.

---

## MCP Server Tools Explained

The server automatically generates four types of tools for each SAP OData entity it discovers:

### Tool Naming Pattern

`{operation}-{serviceId}-{entityName}`

Example: `r-API_BUSINESS_PARTNER-BusinessPartner`

### Four Tool Types

- **Read (r-):** Query entities with filtering, sorting, and pagination. Supports both collection queries and single entity retrieval by key
- **Create (c-):** Create new entities with validation against the OData metadata schema
- **Update (u-):** Modify existing entities using PATCH operations for partial updates
- **Delete (d-):** Remove entities by their unique identifier

### How Tools Are Generated

1. Server discovers OData services via the catalog API
2. Parses entity metadata and schemas
3. Creates CRUD tools dynamically for each entity
4. Registers tools with the MCP protocol layer

### Natural Language → Tool Execution

| **User Request** | **Tool Called** | **OData Operation** |
| --- | --- | --- |
| "Show me 10 banks" | r-BankService-Bank | GET /BankSet?$top=10 |
| "Create customer John Doe" | c-CustomerService-Customer | POST /CustomerSet |
| "Update bank 123 name" | u-BankService-Bank | PATCH /BankSet('123') |
| "Delete order 456" | d-OrderService-Order | DELETE /OrderSet('456') |

Each tool includes parameter schemas, input validation, and context-aware help text—making them immediately usable by AI agents without additional configuration.

---

## Troubleshooting essentials

- Destination connection fails
    - Double-check URL, user, password, and Proxy Type = Internet
    - Ensure the backend is reachable from the public internet
- No OData services discovered
    - Temporarily set ODATA_ALLOW_ALL=true to test connectivity
    - Adjust ODATA_SERVICE_PATTERNS or switch ODATA_DISCOVERY_MODE
- Deployment hiccups
    - Verify cf target points to correct org and space
    - Re-run npm run build:btp before redeploying
- Token errors
    - Confirm client_id, clientsecret, and token url from the service key
    - Check local system time to avoid JWT validation issues

---

## Security reminders

- Never commit .env or service keys
- Prefer BTP-managed bindings in production
- Keep allowlists tight and rotate credentials periodically

---

## Additional background

If you’re new to SAP BTP and Destinations, here’s a quick refresher on how they fit into this setup and why they’re ideal for MCP deployments.

### What is SAP Business Technology Platform (BTP)?

SAP BTP is SAP’s integrated platform-as-a-service for building, extending, and integrating business applications. It provides database and data management (e.g., SAP HANA Cloud), app development and integration services, analytics, and intelligent technologies such as AI and IoT. It supports multi-cloud deployment, deep SAP and non-SAP integration, and strong security capabilities—all of which make it a solid home for an MCP server.

### Understanding Destinations in SAP BTP

Destinations are managed connection definitions. They centralize URLs, authentication, and additional properties, and they support various auth methods like Basic and OAuth. In this guide, a Destination lets the MCP server reach your SAP backend without hardcoding credentials, and makes environment changes trivial.

---

You now have a clean, secured path from SAP backend → BTP Destination → MCP server → MCP client. Keep iterating on your OData discovery patterns to curate exactly what services your client can see, and you’ll maintain a healthy balance between flexibility and safety.