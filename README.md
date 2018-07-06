# Golink

[go/link](http://go.dcoles.net/link)

A server for creating custom HTTP redirects.

Golinks allow assigning a short name for a URL prefix:

- [go/example](http://go.dcoles.net/example) → http://example.com/foo/

Once created, anything placed after the name will be appended to the resulting URL used for the redirect:

- [go/example/bar](http://go.dcoles.net/example/bar) → http://example.com/foo/bar (`http://example.com/foo/` + `bar`)
- [go/example#test](http://go.dcoles.net/example#test) → http://example.com/foo/#test (`http://example.com/foo/` + `#test`)

If you configure your local DNS server to include the Golink server as `go`, then you can use
[http://go/example](http://go/example) directly in your browser without needing to provide the fully qualified domain
 name (FQDN) of the server.


## Demo

An instance of the server is running at [go.dcoles.net](http://go.dcoles.net).

Here are some links you can try:

- [go/link](http://go.dcoles.net/link) This project
- [go/link/blob/master/doc/sample_database.sql](http://go.dcoles.net/link/blob/master/doc/sample_database.sql) Specific sub-path of this project
- [go/github](http://go.dcoles.net/github) GitHub
- [go/github/dcoles/golink](http://go.dcoles.net/github/dcoles/golink) Specific GitHub project
- [go/pylib/json](http://go.dcoles.net/pylib/json#basic-usage) Python JSON module docs
- [go/pylib/json#basic-usage](http://go.dcoles.net/pylib/json#basic-usage) Link to "Basic Usage" of Python JSON module docs 
- [go/search](http://go.dcoles.net/search) Google Search
- [go/search/Hello+World](http://go.dcoles.net/search/Hello+World) Google Search for `Hello World`


## History

Golinks are something I encountered while working as a Google SRE and found terribly useful. Clearly many ex-Googlers have also
agreed, with the same basic idea having been [re-implemented for use in many large tech companies](https://twitter.com/isaach/status/668645946717147136).

Here's a list of some known public implementations:

- https://github.com/kellegous/go (go-lang, MIT License)
- https://goatcodes.com (Golinks as-a-service)


## License

[MIT License](LICENSE.txt)
