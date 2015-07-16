function OverviewController($http, $scope, $timeout, $log) {

  $http.get('metadata').then(function(response) {
    _.extend($scope, response.data);
  });

  var loadData = function() {
    $http.get('state').then(function(response) {
      _.extend($scope, response.data);
      $timeout(loadData, 5000);
    });
  };

  loadData();

}
