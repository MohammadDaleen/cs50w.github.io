from django import forms
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import *


# create a new listing page (view)
# specify a title for the listing, a text-based description, and what the starting bid should be.
# optionally be able to provide a URL for an image for the listing and/or a category (e.g. Fashion, Toys, Electronics, Home, etc.).
class NewListingForm(forms.Form):
    # Add a title input field (- default: textInput)
    title = forms.CharField()
    # Set label for title input field
    title.label = "Title"
    # Change HTML attrbutes of title input field
    title.widget.attrs.update({"class": "form-control mb-2"})
    
    # Add a description input field (- default: textInput)
    description = forms.CharField()
    # Set label for description input field
    description.label = "Dsescription"
    # Change HTML attrbutes of description input field
    description.widget.attrs.update({"class": "form-control"})
    
    # Add a startingBid input field (- default: NumberInput)
    startingBid = forms.DecimalField(decimal_places=2)
    # Set label for startingBid input field
    startingBid.label = "Starting bid"
    # Change HTML attrbutes of startingBid input field
    startingBid.widget.attrs.update({"class": "form-control"})
    
    # Add a imgURL input field (- default: URLInput)
    imgURL = forms.URLField(required=False, )
    # Set label for imgURL input field
    imgURL.label = "URL for an image for the listing"
    # Change HTML attrbutes of imgURL input field
    imgURL.widget.attrs.update({"class": "form-control"})
    
     # Add a category input field (- default: Select)
    category = forms.ChoiceField(choices=Listing.CATEGORIES)
    # Set label for category input field
    category.label = "Category"
    # Change HTML attrbutes of category input field
    category.widget.attrs.update({"class": "form-control"})


# Active Listings Page (view)
# view all of the currently active auction listings. 
# For each active listing, this page should display (at minimum) 
# the title, description, current price, and photo (if one exists for the listing).
def index(request):
    # Get all listings from database
    listings = Listing.objects.all()
    
    # Get default CATEGORIES
    CATEGORIES = Listing.CATEGORIES
    
    # Create an empty list to store data of listings
    data = []
    
    # Loop len(listings) time
    for listing in listings:
        ''' Get the max bid amount for current listing '''
        if listing.listingBids.all(): # To avoid exceptions 
            # Get all bids.amounts for current listing
            bidsAmounts = listing.listingBids.values_list("amount", flat=True) # flat=True returns List/QuerySet instead of List/QuerySet of 1-tuples
            maxBidAmount = max(bidsAmounts)
        # There is no bids for current listing
        else:
            maxBidAmount = None
        
    
        ''' Get the category of current listing '''
        category = "N/A"
        for KEY, VALUE in CATEGORIES:
            if listing.category == KEY:
                category = VALUE
                
        ''' Restructure data of listings'''
        data.append((listing, maxBidAmount, category))
    
    print(data)
    return render(request, "auctions/index.html", {
        # Pass data of listings
        "data": data
        })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("commerce:index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("commerce:index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("commerce:index"))
    else:
        return render(request, "auctions/register.html")


def newListing(request):
    # Check if method is POST
    if request.method == "POST":
        # Take in the data the user submitted and save it as form
        form = NewListingForm(request.POST)

        # Check if form data is valid (server-side)
        if form.is_valid():
            # Isolate data from the 'cleaned' version of form data
            title = form.cleaned_data["title"]
            description = form.cleaned_data["description"]
            startingBid = form.cleaned_data["startingBid"]
            imgURL = form.cleaned_data["imgURL"]
            category = form.cleaned_data["category"]

            ''' Validate data ''' 
            if imgURL and category: # All fields are filled
                listing = Listing(title=title, 
                                  description=description, 
                                  startingBid=startingBid,
                                  imgURL=imgURL,
                                  category=category)
            elif imgURL: # Category's field is not filled
                listing = Listing(title=title, 
                                  description=description, 
                                  startingBid=startingBid,
                                  category=category)
            elif category: # Image's URL's field is not filled
                listing = Listing(title=title, 
                                  description=description, 
                                  startingBid=startingBid,
                                  category=category)
            else: # Category's and Image's URL's fields are not filled
                listing = Listing(title=title, 
                                  description=description, 
                                  startingBid=startingBid,)
            
            # Save data in database (Listing(s) table)
            listing.save()
            

            # foo: Redirect user to the new list's page.
            # return HttpResponseRedirect(reverse(f"commerce:listing", args=[title]))
            return HttpResponseRedirect(reverse(f"commerce:index"))

        else:
            # If the form is invalid, re-render the page with existing information.
            return render(request, "auctions/newListing.html", {
                "NewListingForm": form
            })
    
    
    return render(request, "auctions/newListing.html", {
        # The form for new listing
        "NewListingForm": NewListingForm
    })
    

# Listing Page (view)
# view all details about the listing, including the current price for the listing.
'''
    If the user is signed in, the user should be able to add the item to their “Watchlist.” If the item is already on the watchlist, the user should be able to remove it.
    If the user is signed in, the user should be able to bid on the item. The bid must be at least as large as the starting bid, and must be greater than any other bids that have been placed (if any). If the bid doesn’t meet those criteria, the user should be presented with an error.
    If the user is signed in and is the one who created the listing, the user should have the ability to “close” the auction from this page, which makes the highest bidder the winner of the auction and makes the listing no longer active.
    If a user is signed in on a closed listing page, and the user has won that auction, the page should say so.
    Users who are signed in should be able to add comments to the listing page. The listing page should display all comments that have been made on the listing.
'''
def listing(request, id):
    # Get the listing that has the provided id from database
    listing = Listing.objects.get(id=id)
    
    
    ''' Get the max bid amount for this listing '''
    if listing.listingBids.all(): # To avoid exceptions 
        # Get all bids.amounts for current listing
        bidsAmounts = listing.listingBids.values_list("amount", flat=True) # flat=True returns List/QuerySet instead of List/QuerySet of 1-tuples
        maxBidAmount = max(bidsAmounts)
    # There is no bids for this listing
    else:
        maxBidAmount = None
        
    
    ''' Get the category of this listing '''
    category = "N/A"
    for CATEGORY in Listing.CATEGORIES:
        if listing.category == CATEGORY[0]:
            category = CATEGORY[1]


    # If the user is signed in
    if request.user.is_authenticated:
        # try to check if the listing is in the watchlist of the user
        try: 
            if Watchlist.objects.get(watcher=request.user, auction=listing):
                isOnWatchlistOfUser = True
        # the listing is not on the watchlist of the user
        except Watchlist.DoesNotExist:
            isOnWatchlistOfUser = False
            
        
        # render the listing page
        return render(request, "auctions/listing.html", {
            # Pass listing object
            "listing": listing,
            # Pass listing's object
            "category": category,
            # Pass the max bid amount for current listing
            "maxBidAmount": maxBidAmount,
            # Pass the user's watchlist for current listing
            "isOnWatchlist": isOnWatchlistOfUser
    })
    
    # The request method is GET
    return render(request, "auctions/listing.html", {
        # Pass listing object
        "listing": listing,
        # Pass listing's object
        "category": category, 
        # Pass the max bid amount for current listing
        "maxBidAmount": maxBidAmount
    })

# Watchlist: Users who are signed in should be able to visit a Watchlist page, which should display all of the listings that a user has added to their watchlist. Clicking on any of those listings should take the user to that listing’s page.
def watchlist(request):
    
    if request.method == "POST":
        if not request.user.is_authenticated:
            return HttpResponse("Must provide a listing id.")
        
        listingId = request.POST["listingId"]
        if not listingId:
            return HttpResponse("Must be logged in.")
        
        listing = Listing.objects.get(id=listingId)
        watchlist = Watchlist(watcher=request.user, auction=listing)
        watchlist.save()
        return HttpResponseRedirect(reverse(f"commerce:listing", args=(listingId,)))
        

def removeWatchlist(requset):
    pass
# Categories: Users should be able to visit a page that displays a list of all listing categories. Clicking on the name of any category should take the user to a page that displays all of the active listings in that category.


# Django Admin Interface: Via the Django admin interface, a site administrator should be able to view, add, edit, and delete any listings, comments, and bids made on the site.

