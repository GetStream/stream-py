Step 1 - Twirp/Protoc codegen

First read these docs and make sure to follow the recommendations from there @ai-basics.md @ai-webrtc.md

- add the @https://github.com/GetStream/protocol as a git submodule

create a script similar to @generate.sh script called generate_webrtc.sh that does the following things

- update the protocol submodule to its latest version
- generates the service defined in protobuf/video/sfu/signal_rpc using Twirp
- make sure all python dependencies are added to the webrtc group
- the generated code should live in getstream/video/rtc/pb (make sure it has a init.py file)

Step 2 - Implement location discovery

Implement location discovery inside inside rtc/location_discovery.py

This is how the same functionality is implemented in Golang, make sure to keep the same logic and to create integration tests and pure unit tests using pytest

```
package videosdk

import (
	"context"
	"net"
	"net/http"
	"time"

	"github.com/GetStream/kit/v3/logging"
	"github.com/GetStream/kit/v3/stack"
	"github.com/sirupsen/logrus"
)

const (
	HeaderCloudFrontPop  = "X-Amz-Cf-Pop"
	FallbackLocationName = "IAD"
	StreamProdURL        = "https://hint.stream-io-video.com/"
)

type HTTPClient interface {
	Do(req *http.Request) (*http.Response, error)
}

type LocationDiscovery interface {
	Discover(_ context.Context) string
}

type CloudFrontDiscovery struct {
	client     HTTPClient
	url        string
	maxRetries int
	logger     logrus.FieldLogger
}

var locationHttpClient *http.Client

func init() {
	locationHttpClient = &http.Client{
		Transport: &http.Transport{
			DialContext: (&net.Dialer{
				Timeout:   time.Second,
				KeepAlive: 30 * time.Second,
			}).DialContext,
			MaxIdleConns:          10,
			IdleConnTimeout:       10 * time.Second,
			TLSHandshakeTimeout:   1 * time.Second,
			ExpectContinueTimeout: 1 * time.Second,
		},
		Timeout: time.Second,
	}
}

func NewCloudFrontDiscovery(url string, maxRetries int, client HTTPClient, logger logrus.FieldLogger) *CloudFrontDiscovery {
	return &CloudFrontDiscovery{
		url:        url,
		maxRetries: maxRetries,
		client:     client,
		logger:     logger,
	}
}

func (c *CloudFrontDiscovery) Discover(ctx context.Context) string {
	r, err := http.NewRequestWithContext(ctx, http.MethodHead, c.url, http.NoBody)
	if err != nil {
		logging.LogWarningCtx(ctx, c.logger, stack.Wrap(err))
		return FallbackLocationName
	}

	for i := 0; i < c.maxRetries; i++ {
		c.logger.Infof("Discovering location, attempt %d", i+1)
		resp, err := c.client.Do(r)
		if err != nil {
			logging.LogWarningCtx(ctx, c.logger, stack.Wrapf(err, "HEAD request failed"))
			continue
		}
		if resp.StatusCode != http.StatusOK {
			logging.LogWarningCtx(ctx, c.logger, stack.Errorf("unexpected status code: %d", resp.StatusCode))
			continue
		}
		popName := []rune(resp.Header.Get(HeaderCloudFrontPop))
		_ = resp.Body.Close()

		if len(popName) < 3 {
			logging.LogWarningCtx(ctx, c.logger, stack.Errorf("invalid pop name: %q", string(popName)))
			return FallbackLocationName
		}

		return string(popName[:3])
	}

	return FallbackLocationName
}

```

Make sure to decorate Discover with a cache decorator so we only make the HTTP call once. run the tests you create until they all pass.

- Keep your changes limited to this request, do not implement anythign else in other parts of the codebase
- Use the mock library to test without real http (you can avoid the interface type if not necessary)
- Call CloudFrontDiscovery HTTPHintLocationDiscovery
- If possible use a cache decorator from functools instead of building your own

Step 2 - Implement websocket signaling

Step 3 - Websocket event handling

Step 4 - Websocket automatic reconnection

Step 5 - Join call flow connection manager

Step 6 -
