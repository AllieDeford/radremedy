/* global window, jQuery, google */
/**
 * Creates standard JavaScript utilities in the window.Remedy namespace.
 * 
 * @param  {Window} global The window.
 * @param  {jQuery} $      The jQuery object.
 */
;(function (global, $) {
	'use strict';

	/**
	 * The global namespace for RAD Remedy utilities.
	 * @type {Object}
	 */
	global.Remedy = global.Remedy || {};

	/**
	 * Hides the control-group div that contains the specified element.
	 *
	 * @param  {String} elemId The ID of the element whose control group
	 *                         should be hidden.
	 */
	global.Remedy.hideControlGroup = function (elemId) {
		$(function () {
			$("#" + elemId).parentsUntil("div.control-group").parent().hide();
		});
	};

	/**
	 * Converts the specified input element to a Select2-based item.
	 * 
	 * @param  {String} elemId  The ID of the input element to convert.
	 */
	global.Remedy.makeSelect2 = function (elemId) {
		$(function () {
			var $elem = $("#" + elemId);

			// Store the value for initialization
			var selectVal = $elem.val();

			$elem.select2({
				width: 'inherit'
			}).val(selectVal);
		});
	};

	/**
	 * Resizes the map to fit its parent using a square dimension.
	 * 
	 * @param  {jQuery} $map The jQuery selector for the map element.
	 */
	var sizeMapToParent = function($map) {
		// Get the parent width capped between 320 and 800
		var parentWidth = Math.max(320, Math.min($map.parent().width(), 800));

		$map.width(parentWidth);
		$map.height(parentWidth);
	};

	/**
	 * Renders a Google map containing the specified providers, or hides
	 * it in the event that no providers have been specified.
	 * 
	 * @param  {String} mapId     The ID of the map element.
	 * @param  {Array}  providers The array of providers to show in the map.
	 *                            Each provider should have the properties
	 *                            name, latitude, longitude, address, url, and desc.
	 *
	 * @returns {Boolean} True if providers were found, false otherwise.
	 */
	global.Remedy.showProviderMap = function (mapId, providers) {
		// Make sure we have providers to show.
		if ( providers.length ) {
			$(function () {

				// Scale the map to the size of its parent
				var $map = $("#" + mapId);
				sizeMapToParent($map);

				// Set up the maps and track the bounds
		    var map = new google.maps.Map(document.getElementById(mapId));
		    var bounds = new google.maps.LatLngBounds();
		    var marker;
		    var infoWindow;
		    var i;

		    // Loop through each provider
		    for(i = 0; i < providers.length; i += 1)
		    {
		  		var r = providers[i];

		  		// Create a marker for the provider
		  		marker = new google.maps.Marker({
		      	map: map,
		      	title: r.name,
		      	position: new google.maps.LatLng(r.latitude, r.longitude)
		  		});

		  		// Set up the div of content to display when the marker is clicked
		  		var contentDiv = $("<div />");
		  		$("<a href='" + r.url + "' target='_blank'><strong>" + r.name + "</strong></a><br />").appendTo(contentDiv);
		  		$("<addr><small>" + r.address + "</small></addr><br />").appendTo(contentDiv);
		  		$("<span />").html(r.desc).appendTo(contentDiv);

		  		infoWindow = new google.maps.InfoWindow({
		      	content: contentDiv.html(),
		      	maxWidth: 320
		  		});

		  		// Wire up the click event - we need to wrap this in a closure to ensure
		  		// that clicking different markers doesn't show the same provider - see:
		  		// https://github.com/radremedy/radremedy/issues/229#issuecomment-113010533
		  		google.maps.event.addListener(marker, 'click', (function(marker, infoWindow) {
		  			return function() {
		      		infoWindow.open(map, marker);
		  			}
		  		})(marker, infoWindow));

		  		// Extend our bounds to include this marker
		    	bounds.extend(marker.position);
		    }

    		// Fit our map to these bounds now that all markers have been included.
    		map.fitBounds(bounds);

				// Resize the map in response to window changes
				google.maps.event.addDomListener(window, "resize", function() {
					sizeMapToParent($map);

					var center = map.getCenter();
				 	google.maps.event.trigger(map, "resize");
				 	map.setCenter(center); 
				});    		
			});

			// Indicate we found providers.
			return true;
		}
		else {
			// No providers to show - hide the map's container.
			$(function () {
				$("#" + mapId).parent().hide();
			});

			return false;
		}
	};

	/**
	 * Retrieves the first recognized Google Maps API address component
	 * type from the provided array of types.
	 * 
	 * @param  {Array} types  The array of types to search.
	 * @return {String}       The first recognized component type in the
	 *                        provided array, or an empty string if there
	 *                        was no match.
	 */
	var getAddressComponentType = function (types) {
		// Make sure we have types
    if ( !types || !types.length ) {
      return '';
    }

    // Iterate over each type and see if it's recognized
    for(var typeIdx = 0; typeIdx < types.length; typeIdx += 1) {
      var typeName = types[typeIdx];

      // See if it's one of our recognized types
    	if ($.inArray(typeName, ['locality', 'administrative_area_level_2', 'administrative_area_level_1']) >= 0) {
    		return typeName;
    	}
    }

    // No match found.
    return '';
	};

	/**
	 * Gets a short string representing the location of the provided
	 * Google Maps API place.
	 * 
	 * @param  {google.maps.Place} place The source Google Maps API place.
	 * @return {String}       A short location string, or an empty string
	 *                        if it was not available.
	 */
	var getLocationStr = function(place) {
    var city_str = '';
    var county_str = '';
    var state_str = '';

		// Make sure we have a place with address components
		if( !place || !place.address_components || !place.address_components.length ) {
			return '';
		}

		// Now iterate over each component
    for(var compIdx = 0; compIdx < place.address_components.length; compIdx += 1) {
      var addr_comp = place.address_components[compIdx];
      var name_str = '';
      var comp_type = '';

			/* 
			 * Figure out the name string to use - prefer short_name but
			 * fall back to long_name.
			 */
			name_str = $.trim(addr_comp.short_name) || $.trim(addr_comp.long_name);

      if( !name_str ) {
        return '';
      }

      // Find the type of this address component.
      comp_type = getAddressComponentType(addr_comp.types);

      /* 
       * Now figure out which string to update as a result (city,
       * state, or county)
       */
      switch (comp_type) {
        case 'locality':
        	// Issue #227 - Prefer long_name to short_name
        	// for cities
        	name_str = $.trim(addr_comp.long_name) || name_str;

          city_str = city_str || name_str;
          break;

        case 'administrative_area_level_2':
          county_str = county_str || name_str;
          break;

        case 'administrative_area_level_1':
          state_str = state_str || name_str;
          break;
     	}
    }

    // See if we have a city, and fall back to a county if we have that instead.
    var location_str = city_str || county_str || '';

    // Finally, add the state.
    if (state_str) {
    	// If we already have a city or county, add a comma/space.
      if (location_str ) {
        location_str += ", ";
      }

      location_str += state_str;
    }

    return location_str;
	};

	/**
	 * Initializes a Google Maps autocomplete field and attaches the appropriate
	 * events to update the values of dependent fields.
	 * 
	 * @param  {Boolean} forAddress If true, indicates that the autocomplete should work
	 *                              on addresses instead of general regions.
	 * @param  {String} autoCompId The ID of the element to wire up to the autocomplete.
	 * @param  {String} latId      The ID of the element that stores latitude information.
	 * @param  {String} longId     The ID of the element that stores longitude information.
	 * @param  {String} locationId The ID of the element that stores short location information. Optional.
	 */
	global.Remedy.initMapsAutocomplete = function (forAddress, autoCompId, latId, longId, locationId) {
		var $latitude = $("#" + latId);
		var $longitude = $("#" + longId);
		var $location = $(); // Default to an empty selector
		var autoCompleteTypes = [];

		// See if we have a location field
		if( locationId ) {
			$location = $("#" + locationId);
		}

		// Figure out what we're autocompleting based on forAddress
		if( forAddress ) {
			autoCompleteTypes = ['address'];
		}
		else {
			autoCompleteTypes = ['(regions)'];
		}

		// Now wire stuff up once the document loads
	  $(function () {
	  	// Wire up the initial autocomplete
	    var addrAutoComplete = new google.maps.places.Autocomplete(
	      (document.getElementById(autoCompId)),
	      {
	        types: autoCompleteTypes
	      }
	    );

	    // Listen to changes
	    google.maps.event.addListener(addrAutoComplete, 'place_changed', function() {
	      var place = addrAutoComplete.getPlace();

	      // Make sure we have a place and that it has geocoding information
	      if( place && place.geometry && place.geometry.location ) {
	      	// Truncate latitidue/longitude to 5 digits
	        $latitude.val(place.geometry.location.lat().toFixed(5));
	        $longitude.val(place.geometry.location.lng().toFixed(5));

	        // Also try to get the location, if we're updating that as well
	        if ( $location.length > 0 ) {
	        	$location.val(getLocationStr(place));
	      	}
	      }
	      else {
	        $latitude.val('');
	        $longitude.val('');
	        $location.val('');
	    	}
	    });

			// Invalidate latitude/longitude/location when it's cleared out.
	    $("#" + autoCompId).change(function () {
	      if( !$.trim($(this).val()) ) {
	        $latitude.val('');
	        $longitude.val('');
	        $location.val('');
	      }
	    });
	  });
	};

})(window, jQuery);