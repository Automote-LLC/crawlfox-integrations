const authentication = require("./authentication");
const scrapeAction = require("./creates/scrape");
const searchAction = require("./creates/search");

const addBearer = (request, z, bundle) => {
  if (bundle.authData.apiKey) {
    request.headers.Authorization = `Bearer ${bundle.authData.apiKey}`;
  }
  request.headers["Content-Type"] = "application/json";
  return request;
};

const handleError = (response) => {
  if (response.status >= 400) {
    throw new Error(
      response.content?.message ||
        response.content?.title ||
        `CrawlFox API error (${response.status})`,
    );
  }
  return response;
};

module.exports = {
  version: require("./package.json").version,
  platformVersion: require("zapier-platform-core").version,
  authentication,
  beforeRequest: [addBearer],
  afterResponse: [handleError],
  creates: {
    [scrapeAction.key]: scrapeAction,
    [searchAction.key]: searchAction,
  },
};
