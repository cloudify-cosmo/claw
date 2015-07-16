function OverviewController($http, $scope, $timeout, $log) {

  $http.get('state').then(function(response) {
    var state = response.data;
    $scope.configuration = state.configuration;
    $scope.host = state.host;
    $scope.version = state.version;
    $scope.deployments = state.deployments;
  });

}
