function OverviewController($http, $scope, $timeout, $log) {

  $http.get('state').then(function(response) {
    _.extend($scope, response.data);
  });

}
