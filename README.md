# HeyPhinis
[READ ME IN PROGRESS]
Hey phinis is my final year programming course project.

TL;DR Ran on Flask, HeyPhinis is a user interface for a suggestion algorithm that groups people together and suggests a location to go to.



  HeyPhineas is a unique social network application, aimed at connecting friends with mutual interests and geographical proximity. The application integrates a K-Means algorithm to compute the best location to meet, taking into consideration close-by relevant activities. HeyPhineas makes use of Google Maps API to draw a route and apply directions. It also employs an online database of thousands of locations (parks, restaurants, etc.) and traffic data in order to generate the optimal route for the user.
HeyPhineas uses a K-means implementation along with some degree of K-means, in order to classify a type of activity for a group of people. 
The project itself is run on the user’s browser. A computer that serves as a server hosts the website on the local network, and users are able to connect and view the website by inputting the IPv4 of the server computer and the port 8080 (e.g., 10.0.0.12:8080) into the browser. Running the project on WAN, meaning allowing users outside the local network requires the network operator to open port forwarding on the aforementioned port. 
The design is built for the desktop aspect ratio. While it is possible to add CSS/HTML for mobile users, as was the original plan for this project (to be a mobile app/accessible from the mobile device), since this idea is no longer within the scope of the project the HeyPhineas website is accessible and built specifically for the wider screen, and functionality/visibility of certain elements may be affected by the device’s aspect ratio.


  The rationale behind making HeyPhineas is to solve the often-arising difficulty of choosing activities to spend free time and saving time in the process – making everything accessible within the press of a button. 
I often find myself at a loss when choosing pastime activity, baffled at the number of options. It was specifically at a time like this when a friend and I came up with the idea of HeyPhineas; HeyPhineas promises to be the solution to organizing meetups with friends, planning ahead of traffic, and getting everyone on the same page.
The UI of many such websites is riddled with features and complexity that I have come to find unnecessary. I wanted to build a simplistic website that would answer to my needs while at the same time not going too overboard with over-the-top functionality and graphics. 


  The project relates to the learned materials by implementing encrypted socket communication between a server and its clients over TCP, which was a large part of this, and last year’s material. The server-based communication in this project provides synchronization between users allowing for messaging and a dynamic map showing everyone’s location.
The project also includes thread management. As a user-socket emits an event, the server must open a thread for the function associated with that event and close it upon completion. This makes the server processor heavy, requiring a large number of threads.



