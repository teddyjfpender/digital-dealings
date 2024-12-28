from core.commit_reveal import commit_secret
from core.rng import secret_to_seed, LCG
import matplotlib.pyplot as plt


def main():
    # -------- COMMIT PHASE --------
    print("=== SECRET GENERATION ===")
    #secret = generate_secret()
    secret = b'f#\xe7\xa6+*\x84w\xc3\xe1\x03\xb28\xd0y\xd7\xc9e]\xe6\xc95\xdb\x95\xbe{\x85\x98\xe1\xea\x1f7'
    commitment = commit_secret(secret)
    print("=== COMMIT PHASE ===")
    print(f"Commitment: {commitment}")

    # -------- GAME SETUP --------
    seed = secret_to_seed(secret)
    rng = LCG(seed)

    # Generate 100000 normally distributed random numbers with mean=1.0 and std=0.2
    print("=== RANDOM NUMBERS ===")
    num_samples = 100000
    mu = 1.0
    sigma = 0.2
    normal_values = [rng.random_normal(mu=mu, sigma=sigma) for _ in range(num_samples)]

    # plot the normal values as a normal distribution
    plt.figure(figsize=(8, 6))
    plt.hist(normal_values, bins=20, color="skyblue", edgecolor="black")
    plt.title("Normal Distribution")
    # add note on the bottom left
    plt.figtext(0.4, 0.05, f"N={num_samples}, mu={mu}, sigma={sigma}", ha="right", va="top")
    plt.xlabel("Value")
    plt.ylabel("Frequency")
    plt.grid(axis="y", alpha=0.75)
    plt.savefig("./visualisations/rng_distributions/normal_distribution.png")


if __name__ == "__main__":
    main()
