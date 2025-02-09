import _ from "lodash";

tokenService.$inject = ["$http", "localStorageService"];

/**
 * tokenService - Service for interacting with the token API.
 * @param  {Object} $http               Angular's $http Object.
 * @param  {Object} localStorageService Storage service
 * @return {Object}       Service for interacting with the token API.
 */
export default function tokenService($http, localStorageService) {
  const service = {
    getToken: () => {
      return localStorageService.get("token");
    },
    handleToken: (token) => {
      localStorageService.set("token", token);
      $http.defaults.headers.common.Authorization = "Bearer " + token;
    },
    clearToken: () => {
      localStorageService.remove("token");
      $http.defaults.headers.common.Authorization = undefined;
    },
    getRefresh: () => {
      return localStorageService.get("refresh");
    },
    handleRefresh: (refreshToken) => {
      localStorageService.set("refresh", refreshToken);
    },
    clearRefresh: () => {
      const refreshToken = localStorageService.get("refresh");
      if (refreshToken) {
        // It's possible the refresh token was already removed from the database
        // We usually don't care if that's the case, so set a noop error handler
        localStorageService.remove("refresh");
        return $http
          .post("api/v1/token/revoke", { refresh: refreshToken })
          .catch(() => {});
      }
    },
  };

  _.assign(service, {
    doLogin: (username, password) => {
      return $http
        .post("/api/v1/token", {
          username: username,
          password: password,
        })
        .then((response) => {
          service.handleRefresh(response.data.refresh);
          service.handleToken(response.data.access);
        });
    },
    doRefresh: (refreshToken) => {
      return $http
        .post("/api/v1/token/refresh", { refresh: refreshToken })
        .then(
          (response) => {
            service.handleRefresh(response.data.refresh);
            service.handleToken(response.data.access);
          },
          (response) => {
            service.clearRefresh();
            service.clearToken();
          }
        );
    },
  });

  return service;
}
