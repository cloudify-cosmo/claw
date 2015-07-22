function OverviewController($http, $scope, $timeout, $log) {

  $scope.fetchEvents = function(nodeInstanceId) {
    var executionID = '3a4cd9dd-08f3-499a-afb1-7520d4600939';
    $http.get('/events/'+executionID+'?node_id='+nodeInstanceId).then(
      function(response) {
        $scope.events = response.data.events;
      });
  };

  $http.get('/metadata').then(function(response) {
    $scope.metadata = response.data;
  });

  var loadData = function() {
    $http.get('/state').then(function(response) {
      $scope.deployments = response.data.deployments;
      $timeout(loadData, 5000);
    });
  };

  loadData();

}
