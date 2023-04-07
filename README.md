# docudir
A document management system aimed at being integrated into other systems.

## Core concepts
* Encrypted files at rest
* Configurable on per site basis


## Proposed API

### Site
A site can contain multiple different kinds of documents. A user can own several sites. All sites can have different levels of access.

**Create a new site**
POST `/v1/site/<name>`

**Retrieve information about site, ID, site owner, information about content etc**
GET `/v1/site/<name>`

**Retrieve information about a specific document**
GET `/v1/site/<name>/documents/<document_id>`

**Retrive the actual document**
GET `/v1/site/<name>/documents/<document_id.ext>`

**Access management**

`/v1/site/<name>/access`

**File/folder ID examples**
UUID : `a1ed302a-ff5d-48bb-8cde-15ff9d57c270`
SmallUUID : `7yFBkLpFxQesn7jbg92vRM`


## Background tasks
