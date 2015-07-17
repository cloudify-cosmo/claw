function OverviewController($http, $scope, $timeout, $log) {

  $scope.fetch_events = function(nodeInstanceId) {
    $http.get('/events/3a4cd9dd-08f3-499a-afb1-7520d4600939?node_id='+nodeInstanceId).then(function(response) {
      $scope.events = response.data.events;
    });
  };

  $http.get('/metadata').then(function(response) {
    _.extend($scope, response.data);
  });

  var loadData = function() {
    $http.get('/state').then(function(response) {
      _.extend($scope, response.data);
      $timeout(loadData, 5000);
    });
  };

  loadData();

}
