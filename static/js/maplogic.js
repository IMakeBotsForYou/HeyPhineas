function showSteps(directionResult, markerArray, stepDisplay, map) {
  // For each step, place a marker, and add the text to the marker's infowindow.
  // Also attach the marker to an array so we can keep track of it and remove it
  // when calculating new routes.
  const myRoute = directionResult.routes[0].legs[0];

  for (let i = 0; i < myRoute.steps.length; i++) {
    const marker = (markerArray[i] =
      markerArray[i] || new google.maps.Marker());
    marker.setMap(map);
    marker.setPosition(myRoute.steps[i].start_location);
    attachInstructionText(
      stepDisplay,
      marker,
      myRoute.steps[i].instructions,
      map
    );
  }
}






var onChangeHandler = null;

function initMap() {
  const markerArray = [];
  // Instantiate a directions service.
  const directionsService = new google.maps.DirectionsService();

  // Create a map and center it on my house.
  const map = new google.maps.Map(document.getElementById("map"), {
    zoom: 8,
    center: { lat: 31.894756, lng: 34.809322 },
  });

  socket.on('party_member_coords', function(data){
    for(let i = 0; i < data.length; i++){
        console.log(data);
        var name = data[i][0];
        var latlng = data[i][1];
        var myLatLng = { lat: latlng[0], lng: latlng[1] };
        new google.maps.Marker({
            position: myLatLng,
            title: name,
            map: map
        });
    }
});

  // Create a renderer for directions and bind it to the map.
  const directionsRenderer = new google.maps.DirectionsRenderer({ map: map });
  // Instantiate an info window to hold step text.
  const stepDisplay = new google.maps.InfoWindow();

  onChangeHandler = function () {
    calculateAndDisplayRoute(
      directionsRenderer,
      directionsService,
      markerArray,
      stepDisplay,
      map
    );

};
  // Listen to change events from the start and end lists.
  directionsRenderer.setMap(map); // Existing map object displays directions
}

function calculateAndDisplayRoute(
  directionsRenderer,
  directionsService,
  markerArray,
  stepDisplay,
  map
) {
  // First, remove any existing markers from the map.
  for (let i = 0; i < markerArray.length; i++) {
    markerArray[i].setMap(null);
  }

  // Retrieve the start and end locations and create a DirectionsRequest using
  // WALKING directions.
  a = document.getElementById("secret_end").value;
  console.log("Secret");
  console.log(a);
  if (a == "")
    return;
  var latlng = a.split(", ");
  var lat_ = parseFloat(latlng[0]);
  var lng_ = parseFloat(latlng[1]);

  directionsService
    .route({
      origin: "הנשיא הראשון 52",
      destination: { lat: lat_, lng: lng_ },
      travelMode: google.maps.TravelMode.WALKING,
    })
    .then((result) => {
      // Route the directions and pass the response to a function to create
      // markers for each step.
      var directionsData = result.routes[0] // Get data about the mapped route
      document.getElementById("warnings-panel").innerHTML =
        "<b>" + directionsData.warnings + "</b>";
      directionsRenderer.setDirections(result);
      showSteps(result, markerArray, stepDisplay, map);
      document.getElementById('msg').innerHTML = " Driving distance is " + directionsData.legs[0].distance.text + " (" + directionsData.legs[0].duration.text + ").";

    })
    .catch((e) => {
      window.alert("Directions request failed due to " + e);
    });
}

function attachInstructionText(stepDisplay, marker, text, map) {
  google.maps.event.addListener(marker, "click", () => {
    // Open an info window when the marker is clicked on, containing the text
    // of the step.
    stepDisplay.setContent(text);
    stepDisplay.open(map, marker);
  });
}