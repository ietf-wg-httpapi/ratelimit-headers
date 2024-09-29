---
title: RateLimit header fields for HTTP
abbrev:
docname: draft-ietf-httpapi-ratelimit-headers-latest
category: std

ipr: trust200902
area: Applications and Real-Time
workgroup: HTTPAPI
keyword: Internet-Draft

stand_alone: yes
pi: [toc, tocindent, sortrefs, symrefs, strict, compact, comments, inline, docmapping]

venue:
  group: HTTPAPI
  type: Working Group
  home: https://datatracker.ietf.org/wg/httpapi/about/
  mail: httpapi@ietf.org
  arch: https://mailarchive.ietf.org/arch/browse/httpapi/
  repo: https://github.com/ietf-wg-httpapi/ratelimit-headers

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
 -
    ins: D. Miller
    name: Darrel Miller
    org: Microsoft
    email: darrel@tavis.ca

entity:
  SELF: "RFC nnnn"

normative:
  IANA: RFC8126
  HTTP: RFC9110

informative:
  PRIVACY: RFC6973
  UNIX:
    title: The Single UNIX Specification, Version 2 - 6 Vol Set for UNIX 98
    author:
      name: The Open Group
      ins: The Open Group
    date: 1997-02
--- abstract

This document defines the RateLimit-Policy and RateLimit HTTP header fields for servers to advertise their service policy limits and the current limits, thereby allowing clients to avoid being throttled.

--- middle

# Introduction

Rate limiting of HTTP clients has become a widespread practice, especially for HTTP APIs. Typically, servers who do so limit the number of acceptable requests in a given time window (e.g. 10 requests per second). See {{rate-limiting}} for further information on the current usage of rate limiting in HTTP.

Currently, there is no standard way for servers to communicate quotas so that clients can throttle their requests to prevent errors. This document defines a set of standard HTTP header fields to enable rate limiting:

- RateLimit: to convey
  the server's current limit of quota units available to the client in the policy time window,
  the remaining quota units in the current window,
  and the time remaining in the current window, specified in seconds, and
- RateLimit-Policy: the service policy limits.

These fields enable establishing complex rate limiting policies, including using multiple and variable time windows and dynamic quotas, and implementing concurrency limits.

The behavior of the RateLimit header field is compatible with the delay-seconds notation of Retry-After.

## Goals {#goals}

The goals of this document are:

  Interoperability:
  : Standardize the names and semantics of rate-limit headers
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
  : RateLimit header fields are not meant to support
    authorization or other kinds of access controls.

  Response status code:
  : RateLimit header fields may be returned in both
    successful (see {{Section 15.3 of HTTP}}) and non-successful responses.
    This specification does not cover whether non Successful
    responses count on quota usage,
    nor does it mandates any correlation between the RateLimit values
    and the returned status code.

  Throttling algorithm:
  : This specification does not mandate a specific throttling algorithm.
    The values published in the fields, including the window size,
    can be statically or dynamically evaluated.

  Service Level Agreement:
  : Conveyed quota hints do not imply any service guarantee.
    Server is free to throttle respectful clients under certain circumstances.

## Notational Conventions

{::boilerplate bcp14}

The term Origin is to be interpreted as described in Section 7 of {{!WEB-ORIGIN=RFC6454}}.

This document uses the terms List, Item and Integer from {{Section 3 of !STRUCTURED-FIELDS=RFC8941}} to specify syntax and parsing, along with the concept of "bare item".

# Terminology

## Quota {#quota}

A quota is an allocation of capacity to enable a server to limit client requests. That capacity is counted in quota units and may be reallocated at the end of a time window {{time-window}}.

## Quota Unit {#quota-unit}

A quota unit is the unit of measure used to count the activity of a client.

## Quota Partition {#quota-partition}

A quota partition is a division of a server's capacity across different clients, users and owned resources.

## Time Window {#time-window}

A time window indicates a period of time associated to the allocated quota.

The time window is a non-negative Integer value expressing an interval in seconds, similar to the "delay-seconds" rule defined in {{Section 10.2.3 of HTTP}}. Sub-second precision is not supported.

## Quota Policy {#quota-policy}

A quota policy is maintained by a server to limit the activity (counted in [quota units](#quota-units)) of a given [quota partition](#quota-partition) over a period of time (known as the [time window](#time-window)) to a specified amount known as the [quota](#quota).

Quota policies can be advertised by servers (see {{ratelimit-policy-field}}), but they are not required to be, and more than one quota policy can affect a given request from a client to a server.

## Service Limit {#service-limit}

A service limit is the current limit of the amount of activity that a server will allow based on the remaining quota for a particular quota partition within the time-window, if defined.

# RateLimit-Policy Field {#ratelimit-policy-field}

The "RateLimit-Policy" response header field is a non-empty List of {{quotapolicy-item}}. Its value is informative. The values are expected to remain consistent over a the lifetime of a connection. It is this characteristic that differentiates it from the [RateLimit](#ratelimit-field) that contains values that may change on every request.

~~~
   RateLimit-Policy: burst;q=100;w=60,daily;q=1000;w=86400
~~~

## Quota Policy Item {#quotapolicy-item}
A quota policy Item contains information about a server's capacity allocation for a quota partition associated with the request.

The following parameters are defined in this specification:

  q:
  :  The REQUIRED "q" parameter indicates the quota allocated. ({{ratelimitpolicy-quota}})

  qu:
  :  The OPTIONAL "qu" parameter value conveys the quota units associated to the "q" parameter. The default quota unit is "request". ({{ratelimitpolicy-quotaunit}})

  w:
  :  The OPTIONAL "w" parameter value conveys a time "window" ({{time-window}}). ({{ratelimitpolicy-window}})

  pk:
  :  The OPTIONAL "pk" parameter value conveys the partition key associated to the corresponding request. {{ratelimitpolicy-partitionkey}}

Other parameters are allowed and can be regarded as comments.

Implementation- or service-specific parameters SHOULD be prefixed parameters with a vendor identifier, e.g. `acme-policy`, `acme-burst`.

### Quota Parameter {#ratelimitpolicy-quota}

 The "q" parameter uses a non-negative integer value to indicate the quota allocated for client activity (counted in quota units) for a given quota partition ({{service-limit}}).

### Quota Unit Parameter {#ratelimitpolicy-quotaunit}

The "qu" parameter value conveys the quota units associated to the "q" parameter.

### Window Parameter {#ratelimitpolicy-window}

The "w" parameter value conveys a time "window" in seconds. ({{time-window}}).

### Partition Key Parameter {#ratelimitpolicy-partitionkey}

The "pk" parameter value conveys the partition key associated to the request. Servers MAY use the partition key to divide server capacity across different clients and resources. Quotas are allocated per partition key.

## RateLimit Policy Field Examples

This field MAY convey the time window associated with the expiring-limit, as shown in this example:

~~~
   RateLimit-Policy: default;l=100;w=10
~~~

These examples show multiple policies being returned:

~~~
   RateLimit-Policy: permin;l=50;w=60, perhr;l=1000;w=3600, perday;l=5000;w=86400
~~~

The following example shows a policy with a partition key:

~~~
   RateLimit-Policy: peruser;l=100;w=60;pk=user123
~~~

The following example shows a policy with a partition key and a quota unit:

~~~
   RateLimit-Policy: peruser;l=65535;w=10;pk=user123;qu=bytes
~~~

This field cannot appear in a trailer section.

# RateLimit Field {#ratelimit-field}

A server uses the "RateLimit" response header field to communicate the service limit for a quota policy for a particular partition key.

The field is expressed as List of {{servicelimit-item}}.

~~~
   RateLimit: default;r=50;t=30
~~~

## Service Limit Item {#servicelimit-item}

Each service limit item in identifies the quota policy associated with the request and 

The following parameters are defined in this specification:

  r:
  :  This parameter value conveys the remaining quota units for the identified policy ({{ratelimit-remaining-parameter}}).

  t:
  : This OPTIONAL parameter value conveys the time window reset time for the identified policy ({{ratelimit-reset-parameter}}).

  pk:
  : The OPTIONAL "pk" parameter value conveys the partition key associated to the corresponding request. 

This field cannot appear in a trailer section. Other parameters are allowed and can be regarded as comments.

Implementation- or service-specific parameters SHOULD be prefixed parameters with a vendor identifier, e.g. `acme-policy`, `acme-burst`.


### Remaining Parameter {#ratelimit-remaining-parameter}

The "r" parameter indicates the remaining quota units for the identified policy ({{ratelimit-remaining-parameter}}).

It is a non-negative Integer expressed in [quota units](#quota-units).
Clients MUST NOT assume that a positive remaining value is a guarantee that further requests will be served.
When remaining parameter value is low, it indicates that the server may soon throttle the client (see {{providing-ratelimit-fields}}).

### Reset Parameter {#ratelimit-reset-parameter}

The "t" parameter indicates the number of seconds until the quota associated with the quota policy resets.

It is a non-negative Integer compatible with the delay-seconds rule, because:

- it does not rely on clock synchronization and is resilient to clock adjustment
  and clock skew between client and server (see {{Section 5.6.7 of HTTP}});
- it mitigates the risk related to thundering herd when too many clients are serviced with the same timestamp.

The client MUST NOT assume that all its service limit will be reset at the moment indicated by the reset keyword. The server MAY arbitrarily alter the reset parameter value between subsequent requests; for example, in case of resource saturation or to implement sliding window policies.

### Partition Key Parameter {#ratelimit-partitionkey}

The "pk" parameter value conveys the partition key associated to the request. Servers MAY use the partition key to divide server capacity across different clients and resources. Quotas are allocated per partition key.


## RateLimit Field Examples

This example shows a RateLimit field with a remaining quota of 50 units and a time window reset in 30 seconds:

~~~
   RateLimit: default;r=50;t=30
~~~

This example shows a remaining quota of 999 requests for a partition key that has no time window reset:

~~~
   RateLimit: default;r=999;pk=trial-121323
~~~

This example shows a 300MB remaining quota for an application in the next 60 seconds:

~~~
   RateLimit: default;r=300000000;pk=App-999;t=60;qu=bytes
~~~


# Server Behavior {#providing-ratelimit-fields}

A server MAY return RateLimit header fields independently of the response status code. This includes on throttled responses. This document does not mandate any correlation between the RateLimit header field values and the returned status code.

Servers should be careful when returning RateLimit header fields in redirection responses (i.e., responses with 3xx status codes) because a low remaining keyword value could prevent the client from issuing requests. For example, given the RateLimit header fields below, a client could decide to wait 10 seconds before following the "Location" header field (see {{Section 10.2.2 of HTTP}}), because the remaining keyword value is 0.

~~~ http-message
HTTP/1.1 301 Moved Permanently
Location: /foo/123
RateLimit: problemPolicy;r=0, t=10

~~~

If a response contains both the Retry-After and the RateLimit header fields, the reset keyword value SHOULD reference the same point in time as the Retry-After field value.

A service using RateLimit header fields MUST NOT convey values exposing an unwanted volume of requests and SHOULD implement mechanisms to cap the ratio between the remaining and the reset keyword values (see {{sec-resource-exhaustion}}); this is especially important when a quota policy uses a large time window.

Under certain conditions, a server MAY artificially lower RateLimit header field values between subsequent requests, e.g. to respond to Denial of Service attacks or in case of resource saturation.

## Performance Considerations

Servers are not required to return RateLimit header fields in every response, and clients need to take this into account. For example, an implementer concerned with performance might provide RateLimit header fields only when a given quota is close to exhaustion.

Implementers concerned with response fields' size, might take into account their ratio with respect to the content length, or use header-compression HTTP features such as {{?HPACK=RFC7541}}.


# Client Behavior {#receiving-fields}

The RateLimit header fields can be used by clients to determine whether the associated request respected the server's quota policy, and as an indication of whether subsequent requests will. However, the server might apply other criteria when servicing future requests, and so the quota policy may not completely reflect whether requests will succeed.

For example, a successful response with the following fields:

~~~
   RateLimit: default;r=1;t=7
~~~

does not guarantee that the next request will be successful. Servers' behavior may be subject to other conditions.

A client is responsible for ensuring that RateLimit header field values returned
cause reasonable client behavior with respect to throughput and latency
(see {{sec-resource-exhaustion}} and {{sec-dos}}).

A client receiving RateLimit header fields MUST NOT assume that future responses will contain the same RateLimit header fields, or any RateLimit header fields at all.

Malformed RateLimit header fields MUST be ignored.

A client SHOULD NOT exceed the quota units conveyed by the remaining keyword before the time window expressed in the reset keyword.

The value of the reset keyword is generated at response time: a client aware of a significant network latency MAY behave accordingly and use other information (e.g. the "Date" response header field, or otherwise gathered metrics) to better estimate the reset keyword moment intended by the server.

The details provided in the RateLimit-Policy header field are informative and MAY be ignored.

If a response contains both the RateLimit and Retry-After fields, the Retry-After field MUST take precedence and the reset keyword MAY be ignored.

This specification does not mandate a specific throttling behavior and implementers can adopt their preferred policies, including:

- slowing down or pre-emptively back-off their request rate when
  approaching quota limits;
- consuming all the quota according to the exposed limits and then wait.

## Intermediaries {#intermediaries}

This section documents the considerations advised in {{Section 16.3.2 of HTTP}}.

An intermediary that is not part of the originating service infrastructure and is not aware of the quota policy semantic used by the Origin Server SHOULD NOT alter the RateLimit header fields' values in such a way as to communicate a more permissive quota policy; this includes removing the RateLimit header fields.

An intermediary MAY alter the RateLimit header fields in such a way as to communicate a more restrictive quota policy when:

- it is aware of the quota unit semantic used by the Origin Server;
- it implements this specification and enforces a quota policy which
  is more restrictive than the one conveyed in the fields.

An intermediary SHOULD forward a request even when presuming that it might not be serviced; the service returning the RateLimit header fields is the sole responsible of enforcing the communicated quota policy, and it is always free to service incoming requests.

This specification does not mandate any behavior on intermediaries respect to retries, nor requires that intermediaries have any role in respecting quota policies. For example, it is legitimate for a proxy to retransmit a request without notifying the client, and thus consuming quota units.

[Privacy considerations](#privacy) provide further guidance on intermediaries.

## Caching

{{?HTTP-CACHING=RFC9111}} defines how responses can be stored and reused for subsequent requests,
including those with RateLimit header fields.
Because the information in RateLimit header fields on a cached response may not be current, they SHOULD be ignored on responses that come from cache
(i.e., those with a positive current_age; see {{Section 4.2.3 of HTTP-CACHING}}).

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
RateLimit header fields might reveal the existence of an intermediary
to the user agent.

Where partition keys contain identifying information, either of the client application or the user, servers should be aware of the potential for impersonation and apply the appropriate security mechanisms.

## Remaining quota units are not granted requests {#sec-remaining-not-granted}

RateLimit header fields convey hints from the server
to the clients in order to help them avoid being throttled out.

Clients MUST NOT consider the [quota units](#service-limit) returned in remaining keyword as a service level agreement.

In case of resource saturation, the server MAY artificially lower the returned values
or not serve the request regardless of the advertised quotas.

## Reliability of the reset keyword {#sec-reset-reliability}

Consider that quota might not be restored after the moment referenced by the [reset keyword](#ratelimit-reset-parameter),
and the reset parameter value may not be constant.

Subsequent requests might return a higher reset parameter value
to limit concurrency or implement dynamic or adaptive throttling policies.

## Resource exhaustion {#sec-resource-exhaustion}

When returning reset values, servers must be aware that
many throttled clients may come back at the very moment specified.

This is true for Retry-After too.

For example, if the quota resets every day at `18:00:00`
and your server returns the reset parameter accordingly

~~~
   Date: Tue, 15 Nov 1994 18:00:00 GMT
   RateLimit: daily;r=1;t=36400
~~~

there's a high probability that all clients will show up at `18:00:00`.

This could be mitigated by adding some jitter to the reset value.

Resource exhaustion issues can be associated with quota policies using a
large time window, because a user agent by chance or on purpose
might consume most of its quota units in a significantly shorter interval.

This behavior can be even triggered by the provided RateLimit header fields.
The following example describes a service
with an unconsumed quota policy of 10000 quota units per 1000 seconds.

~~~
RateLimit-Policy: somepolicy;l=10000;w=1000
RateLimit: somepolicy;r=10000;t=10
~~~

A client implementing a simple ratio between remaining keyword and reset keyword could infer an average throughput of 1000 quota units per second, while the limit keyword conveys a quota-policy with an average of 10 quota units per second.
If the service cannot handle such load, it should return either a lower remaining keyword value or an higher reset keyword value.
Moreover, complementing large time window quota policies with a short time window one mitigates those risks.


### Denial of Service {#sec-dos}

RateLimit header fields may contain unexpected values by chance or on purpose.
For example, an excessively high remaining keyword value may be:

- used by a malicious intermediary to trigger a Denial of Service attack
  or consume client resources boosting its requests;
- passed by a misconfigured server;

or a high reset keyword value could inhibit clients to contact the server (e.g. similarly to receiving "Retry-after: 1000000").

To mitigate this risk, clients can set thresholds that they consider reasonable in terms of quota units, time window, concurrent requests or throughput, and define a consistent behavior when the RateLimit exceed those thresholds.
For example this means capping the maximum number of request per second, or implementing retries when the reset keyword exceeds ten minutes.

The considerations above are not limited to RateLimit header fields, but apply to all fields affecting how clients behave in subsequent requests (e.g. Retry-After).


# Privacy Considerations {#privacy}

Clients that act upon a request to rate limit
are potentially re-identifiable (see {{Section 5.2.1 of PRIVACY}})
because they react to information that might only be given to them.
Note that this might apply to other fields too (e.g. Retry-After).

Since rate limiting is usually implemented in contexts where
clients are either identified or profiled
(e.g. assigning different quota units to different users),
this is rarely a concern.

Privacy enhancing infrastructures using RateLimit header fields
can define specific techniques to mitigate the risks of re-identification.

# IANA Considerations

IANA is requested to update one registry and create one new registry.

Please add the following entries to the
"Hypertext Transfer Protocol (HTTP) Field Name Registry" registry ({{HTTP}}):

|---------------------|-----------|---------------|
| Field Name          | Status    | Specification |
|---------------------|-----------|---------------|
| RateLimit           | permanent | {{ratelimit-field}} of {{&SELF}}       |
| RateLimit-Policy    | permanent | {{ratelimit-policy-field}} of {{&SELF}}      |
|---------------------|-----------|---------------|


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

## Interoperability issues

A major interoperability issue in throttling is the lack of standard headers, because:

- each implementation associates different semantics to the
  same header field names;
- header field names proliferates.

User agents interfacing with different servers may thus need to process different headers,
or the very same application interface that sits behind different reverse proxies
may reply with different throttling headers.

# Examples

## Responses without defining policies

Some servers may not expose the policy limits in the RateLimit-Policy header field. Clients can still use the RateLimit header field to throttle their requests.

### Throttling information in responses

The client exhausted its quota for the next 50 seconds.
The limit and time-window is communicated out-of-band.

Request:

~~~ http-message
GET /items/123 HTTP/1.1
Host: api.example

~~~

Response:

~~~ http-message
HTTP/1.1 200 Ok
Content-Type: application/json
RateLimit: default;r=0;t=50

{"hello": "world"}
~~~

Since the field values are not necessarily correlated with
the response status code,
a subsequent request is not required to fail.
The example below shows that the server decided to serve the request
even if remaining keyword value is 0.
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
RateLimit: default;r=0;t=48

{"still": "successful"}
~~~

### Multiple policies in response 

The server uses two different policies to limit the client's requests:

- 5000 daily quota units;
- 1000 hourly quota units.

The client consumed 4900 quota units in the first 14 hours.

Despite the next hourly limit of 1000 quota units,
the closest limit to reach is the daily one.

The server then exposes the RateLimit header fields to
inform the client that:

- it has only 100 quota units left in the daily quota and the window will reset in 10 hours;

The server MAY choose to omit returning the hourly policy as it uses the same quota units as the daily policy and the daily policy is the one that is closest to being exhausted.

Request:

~~~ http-message
GET /items/123 HTTP/1.1
Host: api.example

~~~

Response:

~~~ http-message
HTTP/1.1 200 Ok
Content-Type: application/json
RateLimit: dayLimit;r=100;t=36000

{"hello": "world"}
~~~

### Use for limiting concurrency {#use-for-limiting-concurrency}

RateLimit header fields may be used to limit concurrency,
advertising limits that are lower than the usual ones
in case of saturation, thus increasing availability.

The server adopted a basic policy of 100 quota units per minute,
and in case of resource exhaustion adapts the returned values
reducing both limit and remaining keyword values.

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
RateLimit-Policy: basic;l=100;w=60
RateLimit: basic;r=60;t=58

{"elapsed": 2, "issued": 40}
~~~

At the subsequent request - due to resource exhaustion -
the server advertises only `r=20`.

Request:

~~~ http-message
GET /items/123 HTTP/1.1
Host: api.example

~~~

Response:

~~~ http-message
HTTP/1.1 200 Ok
Content-Type: application/json
RateLimit-Policy: basic;l=100;w=60
RateLimit: basic;r=20;t=56

{"elapsed": 4, "issued": 41}
~~~

### Use in throttled responses

A client exhausted its quota and the server throttles it
sending Retry-After.

In this example, the values of Retry-After and RateLimit header field reference the same moment,
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
RateLimit: default;r=0;t=5

{
"title": "Too Many Requests",
"status": 429,
"detail": "You have exceeded your quota"
}
~~~

## Responses with defined policies

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
RateLimit: fixedwindow;r=99;t=50
RateLimit-Policy: fixedwindow;l=100;w=60
{"hello": "world"}
~~~


### Dynamic limits with parameterized windows

The policy conveyed by the RateLimit header field states that
the server accepts 100 quota units per minute.

To avoid resource exhaustion, the server artificially lowers
the actual limits returned in the throttling headers.

The remaining keyword then advertises
only 9 quota units for the next 50 seconds to slow down the client.

Note that the server could have lowered even the other
values in the RateLimit header field: this specification
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
RateLimit-Policy: dynamic;l=100;w=60
RateLimit: dynamic;r=9;t=50


{
  "status": 200,
  "detail": "Just slow down without waiting."
}
~~~

### Dynamic limits for pushing back and slowing down

Continuing the previous example, let's say the client waits 10 seconds and
performs a new request which, due to resource exhaustion, the server rejects
and pushes back, advertising `r=0` for the next 20 seconds.

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
RateLimit-Policy: dynamic;l=15;w=20
RateLimit: dynamic;r=0;t=20

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
RateLimit-Policy: dynamic;l=100;w=60
RateLimit: dynamic;r=15;t=40

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

The server does not expose remaining values
(for example, because the underlying counters are not available).
Instead, it resets the limit counter every second.

It communicates to the client the limit of 10 quota units per second
always returning the limit and reset keywords.

Request:

~~~ http-message
GET /items/123 HTTP/1.1
Host: api.example

~~~

Response:

~~~ http-message
HTTP/1.1 200 Ok
Content-Type: application/json
RateLimit-Policy: quota;l=100;w=1
RateLimit: quota;t=1

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
RateLimit-Policy: quota;l=10
RateLimit: quota;t=1

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

The server then exposes the RateLimit header fields to inform the client that:

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
RateLimit-Policy: hour;l=1000;w=3600, day;l=5000;w=86400
RateLimit: day;r=100;t=36000

{"hello": "world"}
~~~

# FAQ
{:numbered="false" removeinrfc="true"}

1. Why defining standard fields for throttling?

   To simplify enforcement of throttling policies and enable clients to constraint their requests to avoid being throttled.

2. Can I use RateLimit header fields in throttled responses (eg with status code 429)?

   Yes, you can.

3. Are those specs tied to RFC 6585?

   No. {{?RFC6585}} defines the `429` status code and we use it just as an example of a throttled request,
   that could instead use even `403` or whatever status code.
   
4. Why is the partition key necessary?

   Without a partition key, a server can only effectively only have one scope (aka partition), which is impractical for most services, or it needs to communicate the scopes out-of-band.
   This prevents the development of generic connector code that can be used to prevent requests from being throttled.
   Many APIs rely on API keys, user identity or client identity to allocate quota.
   As soon as a single client processes requests for more than one partition, the client needs to know the corresponding partition key to properly track requests against allocated quota.

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

6. Shouldn't I limit concurrency instead of request rate?

   You can use this specification to limit concurrency
   at the HTTP level (see {#use-for-limiting-concurrency})
   and help clients to shape their requests avoiding being throttled out.

   A problematic way to limit concurrency is connection dropping,
   especially when connections are multiplexed (e.g. HTTP/2)
   because this results in unserviced client requests,
   which is something we want to avoid.

   A semantic way to limit concurrency is to return 503 + Retry-After
   in case of resource saturation (e.g. thrashing, connection queues too long,
   Service Level Objectives not meet, ..).
   Saturation conditions can be either dynamic or static: all this is out of
   the scope for the current document.

7. Do a positive value of remaining paramter imply any service guarantee for my
   future requests to be served?

   No. FAQ integrated in {{ratelimit-remaining-parameter}}.

8. Is the quota-policy definition {{quota-policy}} too complex?

   You can always return the simplest form

~~~
RateLimit:default;r=50;t=60
~~~

   The policy key clearly connects the current usage status of a policy to the defined limits.
   So for the following field:

~~~
RateLimit-Policy: sliding;l=100;w=60;burst=1000;comment="sliding window", fixed;l=5000;w=3600;burst=0;comment="fixed window"
RateLimit: sliding;r=50;t=44
~~~

   the value "sliding" identifies the policy being reported.

9. Can intermediaries alter RateLimit header fields?

    Generally, they should not because it might result in unserviced requests.
    There are reasonable use cases for intermediaries mangling RateLimit header fields though,
    e.g. when they enforce stricter quota-policies,
    or when they are an active component of the service.
    In those case we will consider them as part of the originating infrastructure.

10. Why the `w` parameter is just informative?
    Could it be used by a client to determine the request rate?

    A non-informative `w` parameter might be fine in an environment
    where clients and servers are tightly coupled. Conveying policies
    with this detail on a large scale would be very complex and implementations
    would be likely not interoperable. We thus decided to leave `w` as
    an informational parameter and only rely on the limit, remaining and reset keywords
    for defining the throttling
    behavior.

11. Can I use RateLimit fields in trailers?
    Servers usually establish whether the request is in-quota before creating a response, so the RateLimit field values should be already available in that moment.
    Supporting trailers has the only advantage that allows to provide more up-to-date information to the client in case of slow responses.
    However, this complicates client implementations with respect to combining fields from headers and accounting for intermediaries that drop trailers.
    Since there are no current implementations that use trailers, we decided to leave this as a future-work.

# RateLimit header fields currently used on the web
{:numbered="false" removeinrfc="true"}

Commonly used header field names are:

- `X-RateLimit-Limit`,
  `X-RateLimit-Remaining`,
  `X-RateLimit-Reset`;

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

The semantic of RateLimit depends on the windowing algorithm.
A sliding window policy for example, may result in having a remaining keyword value related to the ratio between the current and the maximum throughput.
e.g.

~~~
RateLimit-Policy: sliding;l=12;w=1
RateLimit: sliding;l=12;r=6;t=1          ; using 50% of throughput, that is 6 units/s

~~~

If this is the case, the optimal solution is to achieve

~~~
RateLimit-Policy: sliding;l=12;w=1
RateLimit: sliding;l=12;r=1;t=1          ; using 100% of throughput, that is 12 units/s
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

In addition to the people above, this document owes a lot to the extensive discussion in the HTTPAPI workgroup, including
Rich Salz,
Darrel Miller
and Julian Reschke.

# Changes
{:numbered="false" removeinrfc="true"}

## Since draft-ietf-httpapi-ratelimit-headers-07
{:numbered="false" removeinrfc="true"}

* Refactored both fields to lists of Items that identify policy and use parameters
* Added quota unit parameter
* Added partition key parameter


## Since draft-ietf-httpapi-ratelimit-headers-03
{:numbered="false" removeinrfc="true"}

* Split policy informatiom in RateLimit-Policy #81


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
