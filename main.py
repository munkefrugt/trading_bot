# from get_data import fetch_btc_data
# from plot import plot_btc_close

# def main():
#     btc_data = fetch_btc_data()
#     print(btc_data.head())
#     print(btc_data.info())
#     plot_btc_close(btc_data)

# if __name__ == "__main__":
#     main()

from get_data import fetch_btc_data
from analyse import compute_heikin_ashi
from plot import plot_heikin_ashi

def main():
    btc_data = fetch_btc_data()
    ha_data = compute_heikin_ashi(btc_data)
    plot_heikin_ashi(ha_data)

if __name__ == "__main__":
    main()


