---
title: RateLimit Fields for HTTP
abbrev:
docname: draft-ietf-httpapi-ratelimit-headers-latest
category: std

ipr: trust200902
area: Applications and Real-Time
workgroup: HTTPAPI
keyword: Internet-Draft

stand_alone: yes
pi: [toc, tocindent, sortrefs, symrefs, strict, compact, comments, inline, docmapping]

author:
 -
    ins: R. Polli
    name: Roberto Polli
    org: Team Digitale, Italian Government
    email: robipolli@gmail.com
    country: Italy
 -
    ins: A. Martinez
    name: Alejandro Martinez Ruiz
    org: Red Hat
    email: alex@flawedcode.org

entity:
  SELF: "RFC nnnn"

normative:
  IANA: RFC8126
  HTTP: RFC9110

informative:
  DNS-PRIVACY: RFC9076
  UNIX:
    title: The Single UNIX Specification, Version 2 - 6 Vol Set for UNIX 98
    author:
      name: The Open Group
      ins: The Open Group
    date: 1997-02

--- abstract

This document defines the RateLimit-Limit, RateLimit-Remaining, RateLimit-Reset and RateLimit-Policy HTTP fields for servers to advertise their current service rate limits, thereby allowing clients to avoid being throttled.

--- note_Note_to_Readers

*RFC EDITOR: please remove this section before publication*

Discussion of this draft takes place on the HTTPAPI working group mailing list (httpapi@ietf.org), which is archived at <https://mailarchive.ietf.org/arch/browse/httpapi/>.

The source code and issues list for this draft can be found at <https://github.com/ietf-wg-httpapi/ratelimit-headers>.

--- middle

# Introduction

Rate limiting HTTP clients has become a widespread practice, especially for HTTP APIs. Typically, servers who do so limit the number of acceptable requests in a given time window (e.g. 10 requests per second). See {{rate-limiting}} for further information on the current usage of rate limiting in HTTP.

Currently, there is no standard way for servers to communicate quotas so that clients can throttle its requests to prevent errors. This document defines a set of standard HTTP fields to enable rate limiting:

- RateLimit-Limit: the server's quota for requests by the client in the time window,
- RateLimit-Remaining: the remaining quota in the current window,
- RateLimit-Reset: the time remaining in the current window, specified in seconds, and
- RateLimit-Policy: the quota policy.

These fields allow the establishment of complex rate limiting policies, including using multiple and variable time windows and dynamic quotas, and implementing concurrency limits.

The behavior of the RateLimit-Reset field is compatible with the delay-seconds notation of Retry-After.


## Goals {#goals}

The goals of this document are:

  Interoperability:
  : Standardization of the names and semantics of rate-limit headers
    to ease their enforcement and adoption;

  Resiliency:
  : Improve resiliency of HTTP infrastructure by
    providing clients with information useful
    to throttle their requests and
    prevent 4xx or 5xx responses;

  Documentation:
  : Simplify API documentation by eliminating the need
    to include detailed quota limits
    and related fields in API documentation.

The following features are out of the scope of this document:

  Authorization:
  : RateLimit fields are not meant to support
    authorization or other kinds of access controls.

  Throttling scope:
  : This specification does not cover the throttling scope,
    that may be the given resource-target, its parent path or the whole
    Origin (see {{Section 7 of !WEB-ORIGIN=RFC6454}}).
    This can be addressed using extensibility mechanisms
    such as the parameter registry {{iana-ratelimit-parameters}}.

  Response status code:
  : RateLimit fields may be returned in both
    successful (see {{Section 15.3 of HTTP}}) and non-successful responses.
    This specification does not cover whether non Successful
    responses count on quota usage,
    nor it mandates any correlation between the RateLimit values
    and the returned status code.

  Throttling policy:
  : This specification does not mandate a specific throttling policy.
    The values published in the fields, including the window size,
    can be statically or dynamically evaluated.

  Service Level Agreement:
  : Conveyed quota hints do not imply any service guarantee.
    Server is free to throttle respectful clients under certain circumstances.

## Notational Conventions

{::boilerplate bcp14}

This document uses the Augmented BNF defined in {{!RFC5234}} and updated by {{!RFC7405}} along with the "#rule" extension defined in {{Section 5.6.1 of HTTP}}.

The term Origin is to be interpreted as described in Section 7 of {{WEB-ORIGIN}}.

This document uses the terms List, Item and Integer from {{Section 3 of !STRUCTURED-FIELDS=RFC8941}} to specify syntax and parsing, along with the concept of "bare item".

The fields defined in this document are collectively referred to as "RateLimit fields".

# Concepts

## Quota Policy {#quota-policy}

A quota policy is described in terms of [quota units](#service-limit) and a [time window](#time-window). It is an Item whose bare item is a [service limit](#service-limit), along with associated Parameters.

The following parameters are defined in this specification:

  w:
  :  The REQUIRED "w" parameter value conveys
     a time window value as defined in {{time-window}}.

Other parameters are allowed and can be regarded as comments. They ought to be registered within the "Hypertext Transfer Protocol (HTTP) RateLimit Parameters Registry", as described in {{iana-ratelimit-parameters}}.

For example, a quota policy of 100 quota units per minute:

~~~ example
   100;w=60
~~~

The definition of a quota policy does not imply any specific distribution of quota units within the time window. If applicable, these details can be conveyed as extension parameters.

For example, two quota policies containing further details via extension parameters:

~~~ example
   100;w=60;comment="fixed window"
   12;w=1;burst=1000;policy="leaky bucket"
~~~

To avoid clashes, implementers SHOULD prefix unregistered parameters with an `x-<vendor>` identifier, e.g. `x-acme-policy`, `x-acme-burst`. While it is useful to define a clear syntax and semantics even for custom parameters, it is important to note that user agents are not required to process quota policy information.

## Time Window {#time-window}

Rate limit policies limit the number of acceptable requests within a given time interval, known as a time window.

The time window is a non-negative Integer value expressing that interval in seconds, similar to the "delay-seconds" rule defined in {{Section 10.2.3 of HTTP}}. Subsecond precision is not supported.

## Service Limit {#service-limit}

The service limit is associated with the maximum number of requests that the server is willing to accept from one or more clients on a given basis (originating IP, authenticated user, geographical, ..) during a [time window](#time-window).

The service limit is a non-negative Integer expressed in quota units.

The service limit SHOULD match the maximum number of acceptable requests.
However, the service limit MAY differ from the total number of acceptable requests when weight mechanisms, bursts, or other server policies are implemented.

If the service limit does not match the maximum number of acceptable requests the relation with that SHOULD be communicated out-of-band.

Example: A server could

- count once requests like `/books/{id}`
- count twice search requests like `/books?author=WuMing`

so that we have the following counters

~~~ example
GET /books/123           ; service-limit=4, remaining: 3, status=200
GET /books?author=WuMing ; service-limit=4, remaining: 1, status=200
GET /books?author=Eco    ; service-limit=4, remaining: 0, status=429
~~~


# RateLimit Field Definitions

The following RateLimit response fields are defined.

## RateLimit-Limit {#ratelimit-limit-field}

The "RateLimit-Limit" response field indicates the [service limit](#service-limit) associated with the client in the current [time window](#time-window). If the client exceeds that limit, it MAY not be served.

The field is an Item and its value is a non-negative Integer referred to as the "expiring-limit". Parameters are not allowed.

The expiring-limit MUST be set to the service limit that is closest to reaching its limit, and the associated time window MUST either be:

- inferred by the value of RateLimit-Reset field at the moment of the reset, or
- communicated out-of-band (e.g. in the documentation).

The RateLimit-Policy field (see {{ratelimit-policy-field}}), might contain information on the associated time window.

~~~ example
   RateLimit-Limit: 100
~~~

This field MUST NOT occur multiple times and can be sent in a trailer section.

## RateLimit-Policy {#ratelimit-policy-field}

The "RateLimit-Policy" response field indicates the quota policies currently associated with the client. Its value is informative.

The field is a non-empty List of Items. Each item is a [quota policy](#quota-policy).

This field can convey the time window associated with the expiring-limit, as shown in this example:

~~~ example
   RateLimit-Policy: 100;w=10
   RateLimit-Limit: 100
~~~

These examples show multiple policies being returned:

~~~ example
   RateLimit-Policy: 10;w=1, 50;w=60, 1000;w=3600, 5000;w=86400
   RateLimit-Policy: 10;w=1;burst=1000, 1000;w=3600
~~~

This field MUST NOT occur multiple times and can be sent in a trailer section.

## RateLimit-Remaining {#ratelimit-remaining-field}

The "RateLimit-Remaining" field response field indicates the remaining quota units defined in {{service-limit}} associated with the client.

The field is an Item and its value is a non-negative Integer expressed in [quota units](#service-limit). Parameters are not allowed.

This field MUST NOT occur multiple times and can be sent in a trailer section.

Clients MUST NOT assume that a positive RateLimit-Remaining field value is a guarantee that further requests will be served.

A low RateLimit-Remaining field value is like a yellow traffic-light for either the number of requests issued in the time window or the request throughput: the red light may arrive suddenly (see {{providing-ratelimit-fields}}).

For example:

~~~ example
   RateLimit-Remaining: 50
~~~

## RateLimit-Reset {#ratelimit-reset-field}

The "RateLimit-Reset" field response field indicates the number of seconds until the quota resets.

The field is a non-negative Integer compatible with the delay-seconds rule, because:

- it does not rely on clock synchronization and is resilient to clock adjustment
  and clock skew between client and server (see {{Section 5.6.7 of HTTP}});
- it mitigates the risk related to thundering herd when too many clients are serviced with the same timestamp.

This field MUST NOT occur multiple times and can be sent in a trailer section.

An example of RateLimit-Reset field use is below.

~~~ example
   RateLimit-Reset: 50
~~~

The client MUST NOT assume that all its service limit will be reset at the moment indicated by the RateLimit-Reset field. The server MAY arbitrarily alter the RateLimit-Reset field value between subsequent requests; for example, in case of resource saturation or to implement sliding window policies.


# Server Behavior {#providing-ratelimit-fields}

A server uses the RateLimit fields to communicate its quota policies. Sending the RateLimit-Limit and RateLimit-Reset fields is REQUIRED; sending RateLimit-Remaining field is RECOMMENDED.

A server MAY return RateLimit fields independently of the response status code. This includes on throttled responses. This document does not mandate any correlation between the RateLimit field values and the returned status code.

Servers should be careful when returning RateLimit fields in redirection responses (i.e., responses with 3xx status codes) because a low RateLimit-Remaining field value could prevent the client from issuing requests. For example, given the RateLimit fields below, a client could decide to wait 10 seconds before following the "Location" header field (see {{Section 10.2.2 of HTTP}}), because the RateLimit-Remaining field value is 0.

~~~ http-message
HTTP/1.1 301 Moved Permanently
Location: /foo/123
RateLimit-Remaining: 0
RateLimit-Limit: 10
RateLimit-Reset: 10

~~~

If a response contains both the Retry-After and the RateLimit-Reset fields, the RateLimit-Reset field value SHOULD reference the same point in time as the Retry-After field value.

When using a policy involving more than one time window, the server MUST reply with the RateLimit fields related to the time window with the lower RateLimit-Remaining field values.

A service using RateLimit fields MUST NOT convey values exposing an unwanted volume of requests and SHOULD implement mechanisms to cap the ratio between RateLimit-Remaining and RateLimit-Reset field values (see {{sec-resource-exhaustion}}); this is especially important when a quota policy uses a large time window.

Under certain conditions, a server MAY artificially lower RateLimit field values between subsequent requests, e.g. to respond to Denial of Service attacks or in case of resource saturation.

Servers usually establish whether the request is in-quota before creating a response, so the RateLimit field values should be already available in that moment. Nonetheless servers MAY decide to send the RateLimit fields in a trailer section.

## Performance Considerations

Servers are not required to return RateLimit fields in every response, and clients need to take this into account. For example, an implementer concerned with performance might provide RateLimit fields only when a given quota is going to expire.

Implementers concerned with response fields' size, might take into account their ratio with respect to the content length, or use header-compression HTTP features such as {{?HPACK=RFC7541}}.


# Client Behavior {#receiving-fields}

The RateLimit fields can be used by clients to determine whether the associated request respected the server's quota policy, and as an indication of whether subsequent requests will. However, the server might apply other criteria when servicing future requests, and so the quota policy may not completely reflect whether they will succeed.

For example, a successful response with the following fields:

~~~ example
   RateLimit-Limit: 10
   RateLimit-Remaining: 1
   RateLimit-Reset: 7
~~~

does not guarantee that the next request will be successful. Servers' behavior may be subject to other conditions like the one shown in the example from {{service-limit}}.

A client MUST validate the RateLimit fields before using them and check if there are significant discrepancies with the expected ones. This includes a RateLimit-Reset field moment too far in the future (e.g. similarly to receiving "Retry-after: 1000000") or a service-limit too high.

A client receiving RateLimit fields MUST NOT assume that future responses will contain the same RateLimit fields, or any RateLimit fields at all.

Malformed RateLimit fields MAY be ignored.

A client SHOULD NOT exceed the quota units conveyed by the RateLimit-Remaining field before the time window expressed in RateLimit-Reset field.

A client MAY still probe the server if the RateLimit-Reset field is considered too high.

The value of RateLimit-Reset field is generated at response time: a client aware of a significant network latency MAY behave accordingly and use other information (e.g. the "Date" response header field, or otherwise gathered metrics) to better estimate the RateLimit-Reset field moment intended by the server.

The details provided in RateLimit-Policy field are informative and MAY be ignored.

If a response contains both the RateLimit-Reset and Retry-After fields, the Retry-After field MUST take precedence and the RateLimit-Reset field MAY be ignored.

This specification does not mandate a specific throttling behavior and implementers can adopt their preferred policies, including:

- slowing down or preemptively back-off their request rate when
  approaching quota limits;
- consuming all the quota according to the exposed limits and then wait.

## Intermediaries {#intermediaries}

This section documents the considerations advised in {{Section 16.3.2 of HTTP}}.

An intermediary that is not part of the originating service infrastructure and is not aware of the quota policy semantic used by the Origin Server SHOULD NOT alter the RateLimit fields' values in such a way as to communicate a more permissive quota policy; this includes removing the RateLimit fields.

An intermediary MAY alter the RateLimit fields in such a way as to communicate a more restrictive quota policy when:

- it is aware of the quota unit semantic used by the Origin Server;
- it implements this specification and enforces a quota policy which
  is more restrictive than the one conveyed in the fields.

An intermediary SHOULD forward a request even when presuming that it might not be serviced; the service returning the RateLimit fields is the sole responsible of enforcing the communicated quota policy, and it is always free to service incoming requests.

This specification does not mandate any behavior on intermediaries respect to retries, nor requires that intermediaries have any role in respecting quota policies. For example, it is legitimate for a proxy to retransmit a request without notifying the client, and thus consuming quota units.

[Privacy considerations](#privacy) provide further guidance on intermediaries.

## Caching

As is the ordinary case for HTTP caching ({{?HTTP-CACHING=RFC9111}}), a response with RateLimit fields might be cached and re-used for subsequent requests. A cached response containing RateLimit fields does not modify quota counters but could contain stale information. Clients interested in determining the freshness of the RateLimit fields could rely on fields such as the Date header field and on the time window of a quota policy.


# Security Considerations

## Throttling does not prevent clients from issuing requests {#sec-throttling-does-not-prevent}

This specification does not prevent clients from making requests.
Servers should always implement mechanisms to prevent resource exhaustion.

## Information disclosure {#sec-information-disclosure}

Servers should not disclose to untrusted parties operational capacity information
that can be used to saturate its infrastructural resources.

While this specification does not mandate whether non-successful responses consume quota,
if error responses (such as 401 (Unauthorized) and 403 (Forbidden)) count against quota,
a malicious client could probe the endpoint to get traffic information of another user.

As intermediaries might retransmit requests and consume
quota units without prior knowledge of the user agent,
RateLimit fields might reveal the existence of an intermediary
to the user agent.

## Remaining quota units are not granted requests {#sec-remaining-not-granted}

RateLimit fields convey hints from the server
to the clients in order to help them avoid being throttled out.

Clients MUST NOT consider the [quota units](#service-limit) returned in RateLimit-Remaining field as a service level agreement.

In case of resource saturation, the server MAY artificially lower the returned values
or not serve the request regardless of the advertised quotas.

## Reliability of RateLimit-Reset {#sec-reset-reliability}

Consider that service limit might not be restored after the moment referenced by RateLimit-Reset field,
and the RateLimit-Reset field value do not be considered fixed nor constant.

Subsequent requests might return a higher RateLimit-Reset field value
to limit concurrency or implement dynamic or adaptive throttling policies.

## Resource exhaustion {#sec-resource-exhaustion}

When returning RateLimit-Reset field you must be aware that
many throttled clients may come back at the very moment specified.

This is true for Retry-After too.

For example, if the quota resets every day at `18:00:00`
and your server returns the RateLimit-Reset field accordingly

~~~ example
   Date: Tue, 15 Nov 1994 08:00:00 GMT
   RateLimit-Reset: 36000
~~~

there's a high probability that all clients will show up at `18:00:00`.

This could be mitigated by adding some jitter to the field-value.

Resource exhaustion issues can be associated with quota policies using a large time window, because a user agent by chance or on purpose
might consume most of its quota units in a significantly shorter interval.

This behavior can be even triggered by the provided RateLimit fields.
The following example describes a service
with an unconsumed quota policy of 10000 quota units per 1000 seconds.

~~~ example
RateLimit-Limit: 10000
RateLimit-Policy: 10000;w=1000
RateLimit-Remaining: 10000
RateLimit-Reset: 10
~~~

A client implementing a simple ratio between RateLimit-Remaining field and
RateLimit-Reset field could infer an average throughput of 1000 quota units per second,
while the RateLimit-Limit field conveys a quota-policy
with an average of 10 quota units per second.
If the service cannot handle such load, it should return
either a lower RateLimit-Remaining field value
or an higher RateLimit-Reset field value.
Moreover, complementing large time window quota policies with a short time window one mitigates those risks.


### Denial of Service

RateLimit fields may contain unexpected values by chance or on purpose.
For example, an excessively high RateLimit-Remaining field value may be:

- used by a malicious intermediary to trigger a Denial of Service attack
  or consume client resources boosting its requests;
- passed by a misconfigured server;

or a high RateLimit-Reset field value could inhibit clients to contact the server.

Clients MUST validate the received values to mitigate those risks.


# Privacy Considerations {#privacy}

Clients that act upon a request to rate limit
are potentially re-identifiable (see {{Section 7.1 of DNS-PRIVACY}})
because they react to information that might only be given to them.
Note that this might apply to other fields too (e.g. Retry-After).

Since rate limiting is usually implemented in contexts where
clients are either identified or profiled
(e.g. assigning different quota units to different users),
this is rarely a concern.

Privacy enhancing infrastructures using RateLimit fields
can define specific techniques to mitigate the risks of re-identification.

# IANA Considerations

IANA is requested to update one registry and create one new registry.

Please add the following entries to the
"Hypertext Transfer Protocol (HTTP) Field Name Registry" registry ({{HTTP}}):

|---------------------|-----------|---------------|
| Field Name          | Status    | Specification |
|---------------------|-----------|---------------|
| RateLimit-Limit     | permanent | {{ratelimit-limit-field}} of {{&SELF}}       |
| RateLimit-Remaining | permanent | {{ratelimit-remaining-field}} of {{&SELF}}   |
| RateLimit-Reset     | permanent | {{ratelimit-reset-field}} of {{&SELF}}       |
| RateLimit-Policy    | permanent | {{ratelimit-policy-field}} of {{&SELF}}      |
|---------------------|-----------|---------------|


## RateLimit Parameters Registration {#iana-ratelimit-parameters}

IANA is requested to create a new registry to be called
"Hypertext Transfer Protocol (HTTP) RateLimit Parameters Registry",
to be located at
<https://www.iana.org/assignments/http-ratelimit-parameters>.
Registration is done on the advice of a Designated Expert,
appointed by the IESG or their delegate.
All entries are Specification Required ({{IANA, Section 4.6}}).

Registration requests consist of the following information:

- Parameter name:
  The parameter name, conforming to {{STRUCTURED-FIELDS}}.

- Field name:
  The RateLimit field for which the parameter is registered. If a parameter is intended to be used
  with multiple fields, it has to be registered
  for each one.

- Description:
  A brief description of the parameter.

- Specification document:
  A reference to the document that specifies the parameter, preferably
  including a URI that can be used to retrieve a copy of the document.

- Comments (optional):
  Any additional information that can be useful.

The initial contents of this registry should be:

|---|---|---|---|
| Field Name       | Parameter name | Description | Specification | Comments (optional) |
|---|---|---|---|
| RateLimit-Policy | w              | Time window | {{quota-policy}} of {{&SELF}} |       |
|---|---|---|---|

--- back

# Rate-limiting and quotas {#rate-limiting}

Servers use quota mechanisms to avoid systems overload, to ensure an equitable distribution of computational resources or to enforce other policies - e.g. monetization.

A basic quota mechanism limits the number of acceptable requests in a given time window, e.g. 10 requests per second.

When quota is exceeded, servers usually do not serve the request replying instead with a 4xx HTTP status code (e.g. 429 or 403) or adopt more aggressive policies like dropping connections.

Quotas may be enforced on different basis (e.g. per user, per IP, per geographic area, ..) and at different levels. For example, an user may be allowed to issue:

- 10 requests per second;
- limited to 60 requests per minute;
- limited to 1000 requests per hour.

Moreover system metrics, statistics and heuristics can be used to implement more complex policies,
where the number of acceptable requests and the time window are computed dynamically.

To help clients throttling their requests,
servers may expose the counters used to evaluate quota policies via HTTP header fields.

Those response headers may be added by HTTP intermediaries such as API gateways and reverse proxies.

On the web we can find many different rate-limit headers,
usually containing the number of allowed requests in a given time window, and when the window is reset.

The common choice is to return three headers containing:

- the maximum number of allowed requests in the time window;
- the number of remaining requests in the current window;
- the time remaining in the current window expressed in seconds or
  as a timestamp;

### Interoperability issues

A major interoperability issue in throttling is the lack of standard headers, because:

- each implementation associates different semantics to the
  same header field names;
- header field names proliferates.

User agents interfacing with different servers may thus need to process different headers,
or the very same application interface that sits behind different reverse proxies
may reply with different throttling headers.

# Examples

## Unparameterized responses

### Throttling information in responses

The client exhausted its service-limit for the next 50 seconds.
The time-window is communicated out-of-band or inferred by the field values.

Request:

~~~ http-message
GET /items/123 HTTP/1.1
Host: api.example

~~~

Response:

~~~ http-message
HTTP/1.1 200 Ok
Content-Type: application/json
RateLimit-Limit: 100
Ratelimit-Remaining: 0
Ratelimit-Reset: 50

{"hello": "world"}
~~~

Since the field values are not necessarily correlated with
the response status code,
a subsequent request is not required to fail.
The example below shows that the server decided to serve the request
even if RateLimit-Remaining field value is 0.
Another server, or the same server under other load conditions, could have decided to throttle the request instead.

Request:

~~~ http-message
GET /items/456 HTTP/1.1
Host: api.example

~~~

Response:

~~~ http-message
HTTP/1.1 200 Ok
Content-Type: application/json
RateLimit-Limit: 100
Ratelimit-Remaining: 0
Ratelimit-Reset: 48

{"still": "successful"}
~~~

### Use in conjunction with custom fields {#use-with-custom-fields}

The server uses two custom fields,
namely `acme-RateLimit-DayLimit` and `acme-RateLimit-HourLimit`
to expose the following policy:

- 5000 daily quota units;
- 1000 hourly quota units.

The client consumed 4900 quota units in the first 14 hours.

Despite the next hourly limit of 1000 quota units,
the closest limit to reach is the daily one.

The server then exposes the RateLimit fields to
inform the client that:

- it has only 100 quota units left;
- the window will reset in 10 hours.

Request:

~~~ http-message
GET /items/123 HTTP/1.1
Host: api.example

~~~

Response:

~~~ http-message
HTTP/1.1 200 Ok
Content-Type: application/json
acme-RateLimit-DayLimit: 5000
acme-RateLimit-HourLimit: 1000
RateLimit-Limit: 5000
RateLimit-Remaining: 100
RateLimit-Reset: 36000

{"hello": "world"}
~~~

### Use for limiting concurrency {#use-for-limiting-concurrency}

Throttling fields may be used to limit concurrency,
advertising limits that are lower than the usual ones
in case of saturation, thus increasing availability.

The server adopted a basic policy of 100 quota units per minute,
and in case of resource exhaustion adapts the returned values
reducing both RateLimit-Limit and RateLimit-Remaining field values.

After 2 seconds the client consumed 40 quota units

Request:

~~~ http-message
GET /items/123 HTTP/1.1
Host: api.example

~~~

Response:

~~~ http-message
HTTP/1.1 200 Ok
Content-Type: application/json
RateLimit-Limit: 100
RateLimit-Remaining: 60
RateLimit-Reset: 58

{"elapsed": 2, "issued": 40}
~~~

At the subsequent request - due to resource exhaustion -
the server advertises only `RateLimit-Remaining: 20`.

Request:

~~~ http-message
GET /items/123 HTTP/1.1
Host: api.example

~~~

Response:

~~~ http-message
HTTP/1.1 200 Ok
Content-Type: application/json
RateLimit-Limit: 100
RateLimit-Remaining: 20
RateLimit-Reset: 56

{"elapsed": 4, "issued": 41}
~~~

### Use in throttled responses

A client exhausted its quota and the server throttles it
sending Retry-After.

In this example, the values of Retry-After and RateLimit-Reset field reference the same moment,
but this is not a requirement.

The 429 (Too Many Request) HTTP status code is just used as an example.

Request:

~~~ http-message
GET /items/123 HTTP/1.1
Host: api.example

~~~

Response:

~~~ http-message
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Date: Mon, 05 Aug 2019 09:27:00 GMT
Retry-After: Mon, 05 Aug 2019 09:27:05 GMT
RateLimit-Reset: 5
RateLimit-Limit: 100
Ratelimit-Remaining: 0

{
"title": "Too Many Requests",
"status": 429,
"detail": "You have exceeded your quota"
}
~~~

## Parameterized responses

### Throttling window specified via parameter

The client has 99 quota units left for the next 50 seconds.
The time window is communicated by the `w` parameter, so we know the throughput is 100 quota units per minute.

Request:

~~~ http-message
GET /items/123 HTTP/1.1
Host: api.example

~~~

Response:

~~~ http-message
HTTP/1.1 200 Ok
Content-Type: application/json
RateLimit-Limit: 100
RateLimit-Policy: 100;w=60
Ratelimit-Remaining: 99
Ratelimit-Reset: 50

{"hello": "world"}
~~~

### Dynamic limits with parameterized windows

The policy conveyed by the RateLimit-Limit field states that
the server accepts 100 quota units per minute.

To avoid resource exhaustion, the server artificially lowers
the actual limits returned in the throttling headers.

The RateLimit-Remaining field then advertises
only 9 quota units for the next 50 seconds to slow down the client.

Note that the server could have lowered even the other
values in the RateLimit-Limit field: this specification
does not mandate any relation between the field values
contained in subsequent responses.

Request:

~~~ http-message
GET /items/123 HTTP/1.1
Host: api.example

~~~

Response:

~~~ http-message
HTTP/1.1 200 Ok
Content-Type: application/json
RateLimit-Limit: 10
RateLimit-Policy: 100;w=60
Ratelimit-Remaining: 9
Ratelimit-Reset: 50

{
  "status": 200,
  "detail": "Just slow down without waiting."
}
~~~

### Dynamic limits for pushing back and slowing down

Continuing the previous example, let's say the client waits 10 seconds and
performs a new request which, due to resource exhaustion, the server rejects
and pushes back, advertising `RateLimit-Remaining: 0` for the next 20 seconds.

The server advertises a smaller window with a lower limit to slow
down the client for the rest of its original window after the 20 seconds elapse.

Request:

~~~ http-message
GET /items/123 HTTP/1.1
Host: api.example

~~~

Response:

~~~ http-message
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
RateLimit-Limit: 0
RateLimit-Policy: 15;w=20
Ratelimit-Remaining: 0
Ratelimit-Reset: 20

{
  "status": 429,
  "detail": "Wait 20 seconds, then slow down!"
}
~~~

## Dynamic limits for pushing back with Retry-After and slow down

Alternatively, given the same context where the previous example starts, we
can convey the same information to the client via Retry-After, with
the advantage that the server can now specify the policy's nominal limit and
window that will apply after the reset, e.g. assuming the resource exhaustion
is likely to be gone by then, so the advertised policy does not need to be
adjusted, yet we managed to stop requests for a while and slow down the rest of
the current window.

Request:

~~~ http-message
GET /items/123 HTTP/1.1
Host: api.example

~~~

Response:

~~~ http-message
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 20
RateLimit-Limit: 15
RateLimit-Policy: 100;w=60
Ratelimit-Remaining: 15
Ratelimit-Reset: 40

{
  "status": 429,
  "detail": "Wait 20 seconds, then slow down!"
}
~~~

Note that in this last response the client is expected to honor
Retry-After and perform no requests for the specified amount of
time, whereas the previous example would not force the client to stop
requests before the reset time is elapsed, as it would still be free to
query again the server even if it is likely to have the request rejected.

### Missing Remaining information

The server does not expose RateLimit-Remaining field values
(for example, because the underlying counters are not available).
Instead, it resets the limit counter every second.

It communicates to the client the limit of 10 quota units per second
always returning the couple RateLimit-Limit and RateLimit-Reset field.

Request:

~~~ http-message
GET /items/123 HTTP/1.1
Host: api.example

~~~

Response:

~~~ http-message
HTTP/1.1 200 Ok
Content-Type: application/json
RateLimit-Limit: 10
Ratelimit-Reset: 1

{"first": "request"}
~~~

Request:

~~~ http-message
GET /items/123 HTTP/1.1
Host: api.example

~~~

Response:

~~~ http-message
HTTP/1.1 200 Ok
Content-Type: application/json
RateLimit-Limit: 10
Ratelimit-Reset: 1

{"second": "request"}
~~~

### Use with multiple windows

This is a standardized way of describing the policy
detailed in {{use-with-custom-fields}}:

- 5000 daily quota units;
- 1000 hourly quota units.

The client consumed 4900 quota units in the first 14 hours.

Despite the next hourly limit of 1000 quota units, the closest limit
to reach is the daily one.

The server then exposes the RateLimit fields to inform the client that:

- it has only 100 quota units left;
- the window will reset in 10 hours;
- the expiring-limit is 5000.

Request:

~~~ http-message
GET /items/123 HTTP/1.1
Host: api.example

~~~

Response:

~~~ http-message
HTTP/1.1 200 OK
Content-Type: application/json
RateLimit-Limit: 5000
RateLimit-Policy: 1000;w=3600, 5000;w=86400
RateLimit-Remaining: 100
RateLimit-Reset: 36000

{"hello": "world"}
~~~

# FAQ
{:numbered="false" removeinrfc="true"}

1. Why defining standard fields for throttling?

   To simplify enforcement of throttling policies.

2. Can I use RateLimit fields in throttled responses (eg with status code 429)?

   Yes, you can.

3. Are those specs tied to RFC 6585?

   No. {{?RFC6585}} defines the `429` status code and we use it just as an example of a throttled request,
   that could instead use even `403` or whatever status code.
   The goal of this specification is to standardize the name and semantic of three ratelimit fields
   widely used on the internet. Stricter relations with status codes or error response payloads
   would impose behaviors to all the existing implementations making the adoption more complex.

4. Why don't pass the throttling scope as a parameter?

   The word "scope" can have different meanings:
   for example it can be an URL, or an authorization scope.
   Since authorization is out of the scope of this document (see {{goals}}),
   and that we rely only on {{HTTP}}, in {{goals}} we defined "scope" in terms of
   URL.

   Since clients are not required to process quota policies (see {{receiving-fields}}),
   we could add a new "RateLimit-Scope" field to this spec.
   See this discussion on a [similar thread](https://github.com/httpwg/http-core/pull/317#issuecomment-585868767)

   Specific ecosystems can still bake their own prefixed parameters,
   such as `acme-auth-scope` or `acme-url-scope` and ensure that clients process them.
   This behavior cannot be relied upon when communicating between different ecosystems.

   We are open to suggestions: comment on [this issue](https://github.com/ioggstream/draft-polli-ratelimit-headers/issues/70)

5. Why using delay-seconds instead of a UNIX Timestamp?
   Why not using subsecond precision?

   Using delay-seconds aligns with Retry-After, which is returned in similar contexts,
   eg on 429 responses.

   Timestamps require a clock synchronization protocol
   (see {{Section 5.6.7 of HTTP}}).
   This may be problematic (e.g. clock adjustment, clock skew, failure of hardcoded clock synchronization servers,
   IoT devices, ..).
   Moreover timestamps may not be monotonically increasing due to clock adjustment.
   See [Another NTP client failure story](https://community.ntppool.org/t/another-ntp-client-failure-story/1014/)

   We did not use subsecond precision because:

   - that is more subject to system clock correction
     like the one implemented via the adjtimex() Linux system call;
   - response-time latency may not make it worth. A brief discussion on the subject is
     on the [httpwg ml](https://lists.w3.org/Archives/Public/ietf-http-wg/2019JulSep/0202.html)
   - almost all rate-limit headers implementations do not use it.

6. Why not support multiple quota remaining?

   While this might be of some value, my experience suggests that overly-complex quota implementations
   results in lower effectiveness of this policy. This spec allows the client to easily focusing on
   RateLimit-Remaining and RateLimit-Reset.

7. Shouldn't I limit concurrency instead of request rate?

   You can use this specification to limit concurrency
   at the HTTP level (see {#use-for-limiting-concurrency})
   and help clients to
   shape their requests avoiding being throttled out.

   A problematic way to limit concurrency is connection dropping,
   especially when connections are multiplexed (e.g. HTTP/2)
   because this results in unserviced client requests,
   which is something we want to avoid.

   A semantic way to limit concurrency is to return 503 + Retry-After
   in case of resource saturation (e.g. thrashing, connection queues too long,
   Service Level Objectives not meet, ..).
   Saturation conditions can be either dynamic or static: all this is out of
   the scope for the current document.

8. Do a positive value of RateLimit-Remaining field imply any service guarantee for my
   future requests to be served?

   No. FAQ integrated in {{ratelimit-remaining-field}}.

9. Is the quota-policy definition {{quota-policy}} too complex?

   You can always return the simplest form of the 3 fields

~~~ example
RateLimit-Limit: 100
RateLimit-Remaining: 50
RateLimit-Reset: 60
~~~

   The key runtime value is the first element of the list: `expiring-limit`, the others quota-policy are informative.
   So for the following field:

~~~ example
RateLimit-Limit: 100
RateLimit-Policy: 100;w=60;burst=1000;comment="sliding window", 5000;w=3600;burst=0;comment="fixed window"
~~~

   the key value is the one referencing the lowest limit: `100`

11. Can we use shorter names? Why don't put everything in one field?

   The most common syntax we found on the web is `X-RateLimit-*` and
   when starting this I-D [we opted for it](https://github.com/ioggstream/draft-polli-ratelimit-headers/issues/34#issuecomment-519366481)

   The basic form of those fields is easily parseable, even by
   implementers processing responses using technologies like
   dynamic interpreter with limited syntax.

   Using a single field complicates parsing and takes
   a significantly different approach from the existing
   ones: this can limit adoption.

12. Why don't mention connections?

    Beware of the term "connection":
￼
￼   - it is just *one* possible saturation cause. Once you go that path
￼     you will expose other infrastructural details (bandwidth, CPU, .. see {{sec-information-disclosure}})
￼     and complicate client compliance;
￼   - it is an infrastructural detail defined in terms of server and network
￼     rather than the consumed service.
      This specification protects the services first,
      and then the infrastructures through client cooperation (see {{sec-throttling-does-not-prevent}}).
￼
￼   RateLimit fields enable sending *on the same connection* different limit values
￼   on each response, depending on the policy scope (e.g. per-user, per-custom-key, ..)
￼
13. Can intermediaries alter RateLimit fields?

    Generally, they should not because it might result in unserviced requests.
    There are reasonable use cases for intermediaries mangling RateLimit fields though,
    e.g. when they enforce stricter quota-policies,
    or when they are an active component of the service.
    In those case we will consider them as part of the originating infrastructure.

14. Why the `w` parameter is just informative?
    Could it be used by a client to determine the request rate?

    A non-informative `w` parameter might be fine in an environment
    where clients and servers are tightly coupled. Conveying policies
    with this detail on a large scale would be very complex and implementations
    would be likely not interoperable. We thus decided to leave `w` as
    an informational parameter and only rely on RateLimit-Limit,
    RateLimit-Remaining field and RateLimit-Reset field for defining the throttling
    behavior.

# RateLimit fields currently used on the web
{:numbered="false" removeinrfc="true"}

Commonly used header field names are:

- `X-RateLimit-Limit`,
  `X-RateLimit-Remaining`,
    `X-RateLimit-Reset`;
- `X-Rate-Limit-Limit`,
  `X-Rate-Limit-Remaining`,
    `X-Rate-Limit-Reset`.

There are variants too, where the window is specified
in the header field name, eg:

- `x-ratelimit-limit-minute`, `x-ratelimit-limit-hour`, `x-ratelimit-limit-day`
- `x-ratelimit-remaining-minute`, `x-ratelimit-remaining-hour`, `x-ratelimit-remaining-day`

Here are some interoperability issues:

- `X-RateLimit-Remaining` references different values, depending on the implementation:

  * seconds remaining to the window expiration
  * milliseconds remaining to the window expiration
  * seconds since UTC, in UNIX Timestamp [UNIX]
  * a datetime, either `IMF-fixdate` {{HTTP}} or {{?RFC3339}}

- different headers, with the same semantic, are used by different implementers:

  * X-RateLimit-Limit and X-Rate-Limit-Limit
  * X-RateLimit-Remaining and X-Rate-Limit-Remaining
  * X-RateLimit-Reset and X-Rate-Limit-Reset

The semantic of RateLimit-Remaining depends on the windowing algorithm.
A sliding window policy for example may result in having a
RateLimit-Remaining field
value related to the ratio between the current and the maximum throughput.
e.g.

~~~ example
RateLimit-Limit: 12
RateLimit-Policy: 12;w=1
RateLimit-Remaining: 6          ; using 50% of throughput, that is 6 units/s
RateLimit-Reset: 1
~~~

If this is the case, the optimal solution is to achieve

~~~ example
RateLimit-Limit: 12
RateLimit-Policy: 12;w=1
RateLimit-Remaining: 1          ; using 100% of throughput, that is 12 units/s
RateLimit-Reset: 1
~~~

At this point you should stop increasing your request rate.

# Acknowledgements
{:numbered="false"}

Thanks to Willi Schoenborn, Alejandro Martinez Ruiz, Alessandro Ranellucci,
Amos Jeffries,
Martin Thomson,
Erik Wilde and Mark Nottingham for being the initial contributors
of these specifications.
Kudos to the first community implementers:
Aapo Talvensaari,
Nathan Friedly
and Sanyam Dogra.

In addition to the people above, this document owes a lot to the extensive discussion
in the HTTPAPI workgroup, including
Rich Salz,
Darrel Miller
and Julian Reschke.

# Changes
{:numbered="false" removeinrfc="true"}

## Since draft-ietf-httpapi-ratelimit-headers-03
{:numbered="false" removeinrfc="true"}

* Split policy informatio in RateLimit-Policy #81


## Since draft-ietf-httpapi-ratelimit-headers-02
{:numbered="false" removeinrfc="true"}

* Address throttling scope #83

## Since draft-ietf-httpapi-ratelimit-headers-01
{:numbered="false" removeinrfc="true"}

* Update IANA considerations #60
* Use Structured fields #58
* Reorganize document #67

## Since draft-ietf-httpapi-ratelimit-headers-00
{:numbered="false" removeinrfc="true"}

* Use I-D.httpbis-semantics, which includes referencing delay-seconds
  instead of delta-seconds. #5
